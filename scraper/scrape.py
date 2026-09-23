"""Collect impact investing jobs from every source and write docs/jobs.json.

Each run replaces the whole file, so the site always mirrors what is live
on the sources right now. To add a source, write a fetch_<name>() function
that returns a list of job dicts and add it to SOURCES.
"""

import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "jobs.json"
USER_AGENT = "Mozilla/5.0 (compatible; ImpactJobsDigest/1.0)"


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp), resp.headers


def clean(text):
    return html.unescape(re.sub(r"\s+", " ", text or "")).strip()


def fetch_impactalpha():
    jobs, page = [], 1
    while True:
        data, headers = get_json(
            "https://impactalpha.com/wp-json/wp/v2/job-listings"
            f"?per_page=100&page={page}&_fields=link,title,date,meta,class_list"
        )
        for item in data:
            meta = item.get("meta") or {}
            if meta.get("_filled"):
                continue
            job_type = next(
                (c[len("job-type-"):].replace("-", " ").title()
                 for c in item.get("class_list", []) if c.startswith("job-type-")),
                "",
            )
            jobs.append({
                "title": clean(item["title"]["rendered"]),
                "organization": clean(meta.get("_company_name")),
                "location": clean(meta.get("_job_location")),
                "remote": bool(meta.get("_remote_position")),
                "salary": clean(meta.get("_job_salary")),
                "type": job_type,
                "posted": item["date"][:10],
                "url": item["link"],
                "source": "ImpactAlpha",
            })
        if page >= int(headers.get("X-WP-TotalPages", 1)):
            return jobs
        page += 1


SOURCES = {
    "ImpactAlpha": fetch_impactalpha,
}


def main():
    jobs, failed = [], []
    for name, fetch in SOURCES.items():
        try:
            found = fetch()
            print(f"{name}: {len(found)} jobs")
            jobs.extend(found)
        except Exception as exc:
            print(f"{name}: FAILED ({exc})", file=sys.stderr)
            failed.append(name)

    # If every source failed, keep last week's list rather than publishing an empty site.
    if not jobs:
        sys.exit("No jobs collected; leaving existing jobs.json untouched.")

    jobs.sort(key=lambda j: j["posted"], reverse=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": list(SOURCES),
        "failed_sources": failed,
        "jobs": jobs,
    }, indent=1, ensure_ascii=False))
    print(f"Wrote {len(jobs)} jobs to {OUTPUT}")


if __name__ == "__main__":
    main()

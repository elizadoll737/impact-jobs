"""Collect impact investing jobs from every source and write docs/jobs.json.

Each run replaces the whole file, so the site always mirrors what is live
on the sources right now. To add a source, write a fetch_<name>() function
that returns a list of job dicts and add it to SOURCES.
"""

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "jobs.json"
USER_AGENT = "Mozilla/5.0 (compatible; ImpactJobsDigest/1.0)"

# Broad boards (CDFI Job Bank, Impactpool) list many roles outside impact
# investing, so only titles matching these are kept.
INVESTING_TITLE = re.compile(
    r"invest|portfolio|underwrit|lending|lender|loan officer|credit officer|commercial loan|"
    r"capital|fund manager|private equity|venture|asset manag|blended finance|"
    r"climate finance|green finance|impact (invest|fund|capital|financ)|\besg\b|"
    r"origination|\bdeal|acquisition|cdfi|community development|financial inclusion|treasur",
    re.I,
)
# Mostly consumer-banking and program roles that the broad keywords above catch.
EXCLUDED_TITLE = re.compile(
    r"fund ?rais|human capital|teller|member (service|experience)|driver|call center|"
    r"mortgage|servicing|clerk|closer|processor|collection|consumer|branch|sales|"
    r"\bretail\b|legal|treasury (management|services)|deposit|grant|program portfolio",
    re.I,
)
# Employer names that contain a keyword ("IDB Invest - Marketing Consultant").
EMPLOYER_PREFIX = re.compile(r"^IDB Invest\W*", re.I)


def is_investing_role(title):
    title = EMPLOYER_PREFIX.sub("", title)
    return bool(INVESTING_TITLE.search(title)) and not EXCLUDED_TITLE.search(title)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace"), resp.headers


def get_json(url):
    body, headers = get(url)
    return json.loads(body), headers


def clean(text):
    return html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"\s+", " ", text or ""))).strip()


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


# ICM's board doesn't show which member fund posted each job (only a logo),
# so the fund is inferred from the application link's domain.
ICM_FUNDS = {
    "vilcap": "Village Capital",
    "quona": "Quona Capital",
    "apis": "Apis & Heritage Capital",
    "cim-llc": "Community Investment Management",
    "alignedclimatecapital": "Aligned Climate Capital",
    "springlane": "Spring Lane Capital",
    "rosecompanies": "Jonathan Rose Companies",
    "enterprisecommunity": "Enterprise Community Partners",
    "crossboundary": "CrossBoundary",
    "tpgcareers": "TPG Rise",
    "cross-border": "Cross Border Impact Ventures",
}


def fetch_icm():
    page, _ = get("https://www.impactcapitalmanagers.com/member-careers")
    jobs = []
    for block in re.split(r'<div class="\s*summary-item\s', page)[1:]:
        link = re.search(r'href="([^"]+)"\s*class="summary-title-link">(.*?)</a>', block, re.S)
        date = re.search(r'<time[^>]*datetime="([\d-]+)"', block)
        if not link:
            continue
        url, title = link.group(1), clean(link.group(2))
        haystack = (url + " " + block[:1500]).lower()
        org = next((name for key, name in ICM_FUNDS.items() if key in haystack), "ICM member fund")
        jobs.append({
            "title": title,
            "organization": org,
            "location": "",
            "remote": False,
            "salary": "",
            "type": "",
            "posted": date.group(1) if date else "",
            "url": url,
            "source": "Impact Capital Managers",
            "link_label": "View job posting",  # links go to the fund's own posting, not ICM
        })
    if not jobs:
        raise RuntimeError("no listings found; page layout may have changed")
    return jobs


CDFI_MAX_AGE_DAYS = 120  # the job bank keeps some postings up long after they've likely closed


def fetch_cdfi_job_bank():
    api = "https://careers.joboffer.ca/api/search?subsystem_code=ofn&page={}"
    cutoff = (datetime.now() - timedelta(days=CDFI_MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    jobs, page = [], 0
    while True:
        data, _ = get_json(api.format(page))
        for item in data.get("jobs") or []:
            title = clean(item["jobtitle"])
            if not is_investing_role(title) or (item.get("created_at") or "") < cutoff:
                continue
            salary = ""
            if item.get("show_wage") == "1" and item.get("wage_minimum"):
                lo, hi = float(item["wage_minimum"]), float(item.get("wage_maximum") or 0)
                fmt = (lambda v: f"${v:,.2f}") if lo < 1000 else (lambda v: f"${v:,.0f}")
                salary = fmt(lo) + (f" – {fmt(hi)}" if hi > lo else "") + ("/hr" if lo < 1000 else "")
            jobs.append({
                "title": title,
                "organization": clean(item["company"]),
                "location": ", ".join(p for p in (item.get("city"), item.get("state")) if p),
                "remote": item.get("remote") == "1",
                "salary": salary,
                "type": "",
                "posted": (item.get("created_at") or "")[:10],
                "url": f"https://jobseeker.cdfijobs.org/careermeetspurpose/#/job/{item['email_code']}",
                "source": "CDFI Job Bank",
            })
        if data.get("first_result", 0) + len(data.get("jobs") or []) > data.get("total_results", 0):
            return jobs
        page += 1
        time.sleep(0.3)


IMPACTPOOL_QUERIES = ["impact investing", "investment officer", "blended finance"]


def fetch_impactpool():
    jobs = {}
    for query in IMPACTPOOL_QUERIES:
        for page in range(1, 20):
            body, _ = get(
                "https://www.impactpool.org/search?per_page=40"
                f"&page={page}&q={urllib.parse.quote_plus(query)}"
            )
            cards = body.split("<div class='job'>")[1:]
            for card in cards:
                job_id = re.search(r'href="/jobs/(\d+)"', card)
                fields = [clean(t) for t in re.findall(
                    r"type='(?:cardTitle|bodyEmphasis)'>(.*?)<", card, re.S)]
                fields = [f for f in fields if f]
                if not job_id or len(fields) < 2 or not is_investing_role(fields[0]):
                    continue
                location = fields[2] if len(fields) > 2 else ""
                jobs[job_id.group(1)] = {
                    "title": fields[0],
                    "organization": fields[1],
                    "location": location.replace(" | ", " · "),
                    "remote": "remote" in location.lower(),
                    "salary": "",
                    "type": "Internship" if "intern" in fields[0].lower() else "",
                    "posted": "",  # not shown on search results; filled with first-seen date
                    "url": f"https://www.impactpool.org/jobs/{job_id.group(1)}",
                    "source": "Impactpool",
                }
            if len(cards) < 40:
                break
            time.sleep(1)
    return list(jobs.values())


SOURCES = {
    "ImpactAlpha": fetch_impactalpha,
    "Impact Capital Managers": fetch_icm,
    "CDFI Job Bank": fetch_cdfi_job_bank,
    "Impactpool": fetch_impactpool,
}


def main():
    previous = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {}
    prev_sources = previous.get("sources")
    prev_sources = prev_sources if isinstance(prev_sources, dict) else {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    jobs, sources = [], {}
    for name, fetch in SOURCES.items():
        try:
            found = fetch()
            print(f"{name}: {len(found)} jobs")
            sources[name] = {"last_success": now, "ok": True}
        except Exception as exc:
            # Keep this source's jobs from the last run rather than dropping them.
            print(f"{name}: FAILED ({exc}); keeping previous listings", file=sys.stderr)
            found = [j for j in previous.get("jobs", []) if j["source"] == name]
            sources[name] = {"last_success": prev_sources.get(name, {}).get("last_success"), "ok": False}
        sources[name]["count"] = len(found)
        jobs.extend(found)

    if not any(s["ok"] for s in sources.values()):
        sys.exit("Every source failed; leaving existing jobs.json untouched.")

    # Sources without posting dates get the date the job was first seen here,
    # flagged so the site says "Added" rather than "Posted".
    first_seen = {j["url"]: j["posted"] for j in previous.get("jobs", [])}
    today = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d")
    for job in jobs:
        if not job["posted"]:
            job["posted"] = first_seen.get(job["url"]) or today
            job["date_is_added"] = True

    jobs.sort(key=lambda j: j["posted"], reverse=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "updated": now,
        "sources": sources,
        "jobs": jobs,
    }, indent=1, ensure_ascii=False))
    print(f"Wrote {len(jobs)} jobs to {OUTPUT}")


if __name__ == "__main__":
    main()

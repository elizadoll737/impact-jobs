# Impact Investing Jobs

Impact investing jobs from multiple sources, collected into one site.

- **Site:** https://elizadoll737.github.io/impact-jobs/
- **Updates:** every Tuesday at 7pm CT, run from this Mac by launchd (`~/Library/LaunchAgents/com.elizadoll737.impactjobs.plist` → `update.sh`). Each run rebuilds the full list, so jobs that have been filled or taken down drop off. It runs from the Mac rather than GitHub Actions because ImpactAlpha's Cloudflare blocks cloud-server requests. If the Mac is asleep at 7pm it runs on wake; if it's shut down, that week is skipped.
- **Update now:** `./update.sh` (log in `logs/update.log`).
- **Stop weekly updates:** `launchctl bootout gui/$(id -u)/com.elizadoll737.impactjobs` and delete the plist.

## Sources

| Source | How it's collected |
|---|---|
| ImpactAlpha | Public job-listings feed. Summary fields only; each job links back to ImpactAlpha. |
| Impact Capital Managers | Member-careers page (Squarespace). Fund name inferred from the application link (`ICM_FUNDS`); unknown ones show "ICM member fund". |
| CDFI Job Bank (OFN) | Acuspire job API behind the OFN widget. Filtered to investing/lending titles and postings from the last 120 days. |
| Impactpool | Search pages for a few queries, filtered to investing titles. No posting dates, so the site shows the date first added. |

**Not included:** Terra.do (listings mixed with job-spam aggregators). GIIN Career Center and Mission Investors Exchange block automated requests, so the site links to them under "More boards to check".

To add a source, add a `fetch_<name>()` function in `scraper/scrape.py` and register it in `SOURCES`.

## Run locally

```
python3 scraper/scrape.py
cd docs && python3 -m http.server
```

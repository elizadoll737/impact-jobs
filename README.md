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

To add a source, add a `fetch_<name>()` function in `scraper/scrape.py` and register it in `SOURCES`.

## Run locally

```
python3 scraper/scrape.py
cd docs && python3 -m http.server
```

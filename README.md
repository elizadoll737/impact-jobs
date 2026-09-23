# Impact Investing Jobs

Impact investing jobs from multiple sources, collected into one site.

- **Site:** https://elizadoll737.github.io/impact-jobs/
- **Updates:** every Tuesday at 7pm CT (`.github/workflows/update-jobs.yml`). Each run rebuilds the full list, so jobs that have been filled or taken down drop off.
- **Update now:** Actions tab → "Update jobs" → "Run workflow".

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

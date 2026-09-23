# Impact Investing Jobs — notes for Claude

Owner is a non-developer (Kellogg student); explain steps plainly and do the technical work for them.

- Live site: https://elizadoll737.github.io/impact-jobs/ (GitHub Pages, repo `elizadoll737/impact-jobs`, served from `docs/`)
- `scraper/scrape.py` collects every source in `SOURCES` into `docs/jobs.json`. Add a source = new `fetch_<name>()` returning job dicts (title, organization, location, remote, salary, type, posted, url, source) + register it in `SOURCES`. The site's source filter and status pills pick new sources up automatically.
- Weekly update runs from the Mac, not GitHub Actions: launchd job `~/Library/LaunchAgents/com.elizadoll737.impactjobs.plist` runs `update.sh` Tuesdays 7pm CT (Mac is on America/Chicago). Log: `logs/update.log`. Manual update: `./update.sh`.
- GitHub Actions was dropped because ImpactAlpha's Cloudflare returns 403 to cloud-server IPs. New sources that allow datacenter IPs could run on Actions instead; don't try to disguise requests to get past a site's bot blocking.
- `gh` CLI is at `~/.local/bin/gh` (not on PATH; no Homebrew). Logged in as elizadoll737; git pushes use it as credential helper.
- ImpactAlpha job descriptions are subscriber content: show summary fields only and link out ("View on <source>"). Don't republish full descriptions.
- A failed source keeps its previous listings; `sources[name].last_success` records when it last updated and the page shows an orange "didn't update this week" pill.
- Pages serves HTML with `max-age=600`. If you change the shape of `jobs.json`, write it under a new filename (and point `index.html` at it) so a browser's cached old page doesn't break on the new data.

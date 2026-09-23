#!/bin/bash
# Weekly update: collect jobs and publish them to the GitHub Pages site.
# Run automatically every Tuesday at 7pm by launchd
# (~/Library/LaunchAgents/com.elizadoll737.impactjobs.plist), or by hand anytime.
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p logs
exec >> logs/update.log 2>&1
echo "=== $(date) ==="

git pull --rebase --quiet
/usr/bin/python3 scraper/scrape.py
git add docs/jobs.json
if git diff --cached --quiet; then
  echo "No changes to publish."
else
  git commit --quiet -m "Weekly jobs update"
  git push --quiet
  echo "Published."
fi

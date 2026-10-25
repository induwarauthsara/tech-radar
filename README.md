# Tech Radar

A lightweight, GitHub Pages dashboard for daily technology news and GitHub repository discoveries.

**Website:** https://induwarauthsara.github.io/tech-radar/

## What it shows

- Daily technology updates from public RSS feeds and official engineering blogs.
- GitHub trending repositories across daily, weekly, and monthly views.
- Trending GitHub developers as discovery leads.
- A repository history to reduce repeat recommendations.
- Source links and the last successful update time.

## How it works

A scheduled GitHub Actions workflow runs daily around 19:00 Sri Lanka time (13:30 UTC), collects publicly accessible sources, updates JSON under `data/`, and commits the changes. GitHub may delay scheduled workflows, so the displayed timestamp is the actual update time.

The site is a static HTML/CSS/JavaScript app and does not require a database or API key. News summaries are generated from public feed titles/descriptions; they are not AI-generated editorial analysis. Some social platforms restrict unauthenticated access, so this project does not claim to collect private or inaccessible content.

## Enable GitHub Pages

In the repository, open **Settings → Pages** and select **Deploy from a branch**, branch **main**, folder **/(root)**. Save. The first deployment may take a few minutes.

## Run the collector locally

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python scripts/update_radar.py
```

## Data files

- `data/tech-updates.json`: recent news items.
- `data/github-repositories.json`: current repository picks.
- `data/history.json`: previously featured repository URLs, used to avoid repeats.

## Sources

Public GitHub Trending pages, official engineering blogs and public RSS/Atom feeds. Each item links to its source so you can verify the details.

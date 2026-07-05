# ⚽ World Cup 2026 — Results & Predictions

A free, statically-hosted website showing live **2026 FIFA World Cup** scores, group standings, and AI-powered predictions for who will win the tournament.

🔗 **Live site:** https://alext78.github.io/worldcup-2026/

## Features

- **📋 Group Standings** — All 12 groups of 4 teams with W/D/L, GD, points
- **📊 Overview Dashboard** — At-a-glance group summaries and tournament stats  
- **🏆 Predictions** — ELO rating system + 5,000 Monte Carlo tournament simulations
- **📈 Winner Probability Chart** — Bar chart of the top 8 title contenders
- **🔄 Auto-refresh** — Data updates every 6 hours via GitHub Actions
- **📱 Mobile-friendly** — Responsive dark theme, works on any device

## How it works

```
Wikipedia API → Python scraper → data.json → Static HTML + JS → GitHub Pages
                                        ↑
                              GitHub Actions (every 6h)
```

1. **Python scraper** (`scripts/fetch_data.py`) parses Wikipedia's 2026 World Cup page tables
2. **JSON output** written to `data/data.json` with all standings and teams  
3. **Single HTML page** (`index.html`) loads the JSON and renders with Tailwind CSS + Chart.js
4. **ELO ratings** computed client-side from group stage results
5. **Monte Carlo simulation** runs 5,000 tournament simulations in the browser
6. **GitHub Actions** re-scrapes every 6 hours and commits updated data

## Tech Stack

| Layer | Tech |
|-------|------|
| Data | Wikipedia API (Python stdlib) |
| Frontend | HTML, Tailwind CSS (CDN), Chart.js |
| Logic | Vanilla JS (ELO + Monte Carlo) |
| Hosting | GitHub Pages (free) |
| Automation | GitHub Actions (free) |

## Local Development

```bash
# Scrape data
python3 scripts/fetch_data.py

# Serve locally
python3 -m http.server 8000
# Open http://localhost:8000
```

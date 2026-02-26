# News Brief

Automated daily financial newsletter. Fetches news, summarizes with Claude, sends email, and publishes a pretty archive to GitHub Pages.

---

## How it works

Every weekday at 7 AM Mexico City time, GitHub Actions:

1. Fetches articles from NewsAPI across your configured topics
2. Pulls live market data from Yahoo Finance and weather from Open-Meteo
3. Sends everything to Claude, which writes the editor note, picks stories, scores sentiment, and selects a quote
4. Sends the Gmail-safe email to all subscribers
5. Saves a pretty HTML version to `archive/`
6. Commits and pushes back to the repo — GitHub Pages updates automatically


### 2. Enable GitHub Pages

Go to your repo on GitHub:
`Settings → Pages → Source → Deploy from branch → main → /archive`

Your archive will be live at:
`https://YOUR_USERNAME.github.io/mexico-finance-brief`

### 3. Add your secrets

Go to: `Settings → Secrets and variables → Actions → New repository secret`

Add each of these:

| Secret name | Where to get it |
|---|---|
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) — free account |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Google Account → Security → App Passwords |
| `SUBSCRIBERS` | Comma-separated emails: `you@gmail.com,friend@gmail.com` |

### 4. Trigger a test run

Go to: `Actions → Daily Newsletter → Run workflow`

This runs the full pipeline immediately without waiting for 7 AM. Check your inbox and `archive/index.html` after it completes.

---

## Running locally

```bash
cd bot
pip install -r ../requirements.txt

# Set your secrets as environment variables
export NEWS_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export EMAIL_SENDER="..."
export EMAIL_PASSWORD="..."
export SUBSCRIBERS="you@gmail.com"

# Full run
python main.py

# Test email only (no API calls, mock data)
python test_email.py
```

Or create a `.env` file in the `bot/` folder (never committed):
```
NEWS_API_KEY=...
ANTHROPIC_API_KEY=...
EMAIL_SENDER=...
EMAIL_PASSWORD=...
SUBSCRIBERS=you@gmail.com
```

Then load it before running:
```bash
export $(cat .env | xargs) && python main.py
```

---

## Repo structure

```
mexico-finance-brief/
│
├── .github/
│   └── workflows/
│       └── newsletter.yml    ← GitHub Actions schedule + deploy
│
├── bot/                      ← All Python source
│   ├── main.py               ← Entry point
│   ├── config.py             ← Settings (reads secrets from env)
│   ├── fetcher.py            ← NewsAPI + article scraping
│   ├── scraper.py            ← Full article text extractor
│   ├── summarizer.py         ← Claude API call, returns structured JSON
│   ├── market_data.py        ← Yahoo Finance + Open-Meteo
│   ├── storage.py            ← Saves/loads daily digest JSONs
│   ├── renderer.py           ← Gmail-safe email HTML (tables, inline styles)
│   ├── pretty_renderer.py    ← Full-featured HTML for the archive
│   ├── archive.py            ← Saves pretty issues, rebuilds index.html
│   ├── delivery.py           ← Gmail SMTP sender
│   └── test_email.py         ← Sends a test email with mock data
│
├── docs/                     ← Served by GitHub Pages (was: archive/)
│   ├── index.html            ← Auto-rebuilt archive index
│   └── YYYY-MM-DD.html       ← One file per issue
│
├── digests/                  ← Raw JSON per day (for dashboard later)
│   └── YYYY-MM-DD.json
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Adjusting the schedule

Edit `.github/workflows/newsletter.yml`:

```yaml
- cron: "0 13 * * 1-5"   # 7 AM CST (UTC-6), Mon-Fri
- cron: "0 12 * * 1-5"   # 7 AM CDT (UTC-5), summer
```

Mexico City observes daylight saving time from the first Sunday of April to the last Sunday of October.

---

## Cost

| Service | Cost |
|---|---|
| GitHub Actions | Free (2,000 min/month, bot uses ~5 min/day) |
| GitHub Pages | Free |
| NewsAPI | Free (100 req/day) |
| Claude API | ~$0.05–0.08/run (~$25/year) |
| Open-Meteo weather | Free, no key |
| Yahoo Finance | Free, no key |
| Gmail SMTP | Free |

Total: ~$25/year for the Claude API calls.

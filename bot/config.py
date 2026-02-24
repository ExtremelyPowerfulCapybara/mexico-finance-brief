# ─────────────────────────────────────────────
#  config.py  —  Settings + secrets
#
#  Secrets are read from environment variables
#  so they're never committed to the repo.
#  On GitHub Actions they come from repo secrets.
#  Locally, create a .env file or export them
#  in your terminal before running.
# ─────────────────────────────────────────────

import os

# ── Secrets (never commit these) ─────────────
NEWS_API_KEY      = os.environ.get("NEWS_API_KEY",      "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
EMAIL_SENDER      = os.environ.get("EMAIL_SENDER",      "")
EMAIL_PASSWORD    = os.environ.get("EMAIL_PASSWORD",    "")

# Subscribers — comma-separated in the env var
# e.g. SUBSCRIBERS="you@gmail.com,friend@gmail.com"
_subs_env   = os.environ.get("SUBSCRIBERS", EMAIL_SENDER)
SUBSCRIBERS = [s.strip() for s in _subs_env.split(",") if s.strip()]

# ── Newsletter identity (safe to commit) ─────
NEWSLETTER_NAME    = "Mexico Finance Brief"
NEWSLETTER_TAGLINE = "Daily Intelligence"
AUTHOR_NAME        = "Adrian"
AUTHOR_BYLINE      = "Al Gorithm"

# ── News preferences ──────────────────────────
TOPICS                 = ["finance", "economy", "Mexico", "trade", "markets"]
LANGUAGE               = "en"
MAX_ARTICLES_PER_TOPIC = 5
MAX_ARTICLE_CHARS      = 3000

# ── Market tickers (Yahoo Finance symbols) ────
TICKER_SYMBOLS = [
    ("USD/MXN",   "MXN=X"),
    ("S&P 500",   "^GSPC"),
    ("CETES 28D", None),    # placeholder — no free API available
    ("IPC BMV",   "^MXX"),
]

# ── Currency table ────────────────────────────
CURRENCY_PAIRS = ["USD", "EUR", "CAD", "CNY"]

# ── Weather (Open-Meteo, no API key needed) ───
WEATHER_LAT  = 19.4326
WEATHER_LON  = -99.1332
WEATHER_CITY = "Mexico City"

# ── Storage paths ─────────────────────────────
# Paths are relative to the repo root, not bot/
# so digests and archive are committed together.
import pathlib
REPO_ROOT   = pathlib.Path(__file__).parent.parent
DIGEST_DIR  = str(REPO_ROOT / "digests")
ARCHIVE_DIR = str(REPO_ROOT / "docs")

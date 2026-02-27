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
NEWSLETTER_NAME    = "The Opening Bell"
NEWSLETTER_TAGLINE = "Context before the noise"
AUTHOR_NAME        = "Los 3"

# ── Rotating pen names ────────────────────────
AUTHOR_NAMES = [
    "Drew Downing",
    "Cora Lation",
    "Russell Bearings",
    "Hal F. Life",
    "Carrie Trade",
    "Bea Rish",
    "Buck N. Yields",
    "Ray Tio",
    "Stan Dard Deviation",
    "Cliff N. Overhang",
    "Mort I. Fication",
    "Barry Cade",
    "Rex Cession",
    "Hugh Liquidity",
    "Art Bitrage",
    "Bill Ateral",
    "Mac Roeconomics",
    "Lev Erage",
    "Cal Lateral",
    "Phil Ation",
    "Chip Deflation",
    "Vera Tility",
]

AUTHOR_TITLES = [
    "Director of Mildly Concerning Developments",
    "Senior Fellow, Bureau of Controlled Panic",
    "Chairman of the Committee on 'It's Fine'",
    "Principal Strategist, Gradual Decay",
    "Global Head of Conditional Optimism",
    "Custodian of Forward Guidance and Other Myths",
    "Deputy Undersecretary of Controlled Descent",
    "Executive Director of Fragile Equilibrium",
    "Chief Architect of Confident Uncertainty",
    "Senior Fellow, Institute of Permanent Volatility",
    "Visiting Scholar, Department of Inevitable Outcomes",
    "Head of Preemptive Disappointment",
    "Chief Correspondent, Bureau of Things Already Priced In",
    "Director of Soft Landings (Emeritus)",
    "Senior Analyst, Office of Delayed Consequences",
    "Minister of Transitory Phenomena",
    "Head of Quantitative Vibes",
    "Assistant to the Regional Hegemon",
    "Chief of Staff, Monetary Policy Theater",
    "Commissioner of Yield Curve Interpretive Dance",
    "Secretary General of the Ad Hoc Liquidity Committee",
    "Distinguished Chair of Optimism Suppression",
    "Lead Correspondent, The Structural Adjustment Beat",
    "Director of Things That Are Technically Not a Crisis",
    "Senior Vice President of Premature Conclusions",
    "Keeper of the Dot Plot",
    "Ambassador-at-Large for Unintended Consequences",
]

# ── News preferences ──────────────────────────
TOPICS = ["Spain economy", "Spain finance", "euro markets", "Spain trade", "economia España"]
LANGUAGE               = "es"
MAX_ARTICLES_PER_TOPIC = 10
MAX_ARTICLE_CHARS      = 8092

# ── Market tickers (Yahoo Finance symbols) ────
TICKER_SYMBOLS = [
    ("SPX",    "S&P 500"),
    ("^IBEX",    "IBEX 35"),
    ("^STOXX50E", "Euro Stoxx"),
    ("^GDAXI",     "DAX"),
]

# ── Currency table ────────────────────────────
CURRENCY_PAIRS = ["USD", "GBP", "CHF", "JPY"]

# ── Weather (Open-Meteo, no API key needed) ───
WEATHER_LAT  = 40.4168
WEATHER_LON  = -3.7038
WEATHER_CITY = "Madrid"

# ── Storage paths ─────────────────────────────
# Paths are relative to the repo root, not bot/
# so digests and archive are committed together.
import pathlib
REPO_ROOT   = pathlib.Path(__file__).parent.parent
DIGEST_DIR  = str(REPO_ROOT / "digests")
ARCHIVE_DIR = str(REPO_ROOT / "docs")

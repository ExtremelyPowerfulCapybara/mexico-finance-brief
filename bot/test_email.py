# ─────────────────────────────────────────────
#  test_email.py  —  Send a test email with
#  mock data without running the full pipeline.
#  Usage: python test_email.py
# ─────────────────────────────────────────────

from renderer import build_html, build_plain
from delivery import send_email
from archive  import save_pretty_issue

# ── Mock data ─────────────────────────────────

MOCK_TICKERS = [
    {"label": "USD/MXN",   "value": "17.10", "change": "▼ 0.9%", "direction": "down"},
    {"label": "S&P 500",   "value": "6,910",  "change": "▲ 0.4%", "direction": "up"},
    {"label": "CETES 28D", "value": "9.85%",  "change": "",        "direction": "flat"},
    {"label": "IPC BMV",   "value": "71,436", "change": "▲ 0.8%", "direction": "up"},
]

MOCK_CURRENCY = [
    {"pair": "MXN / USD", "rate": "0.0560", "chg_1d": {"text": "▼ 1.21%", "cls": "chg-down"}, "chg_1w": {"text": "▼ 2.04%", "cls": "chg-down"}},
    {"pair": "MXN / EUR", "rate": "0.0516", "chg_1d": {"text": "▼ 0.88%", "cls": "chg-down"}, "chg_1w": {"text": "▼ 1.45%", "cls": "chg-down"}},
    {"pair": "MXN / CAD", "rate": "0.0763", "chg_1d": {"text": "▲ 0.32%", "cls": "chg-up"},   "chg_1w": {"text": "— 0.00%", "cls": "chg-flat"}},
    {"pair": "MXN / CNY", "rate": "0.4068", "chg_1d": {"text": "▼ 0.55%", "cls": "chg-down"}, "chg_1w": {"text": "▲ 0.21%", "cls": "chg-up"}},
]

MOCK_WEATHER = {
    "city":     "Mexico City",
    "high_low": "22°C / 14°C",
    "humidity": "Humidity 65%",
    "desc":     "Clear morning, clouds by afternoon",
}

MOCK_DIGEST = {
    "editor_note": "Rough day for the peso. Fed minutes came in more hawkish than expected and markets didn't love it. Three things worth your attention today, starting with what the SHCP didn't say in this morning's press release.",

    "sentiment": {
        "label":   "Risk-Off",
        "context": "Hawkish Fed minutes and peso weakness dominate today's narrative. Markets are pricing in fewer rate cuts through H1.",
    },

    "stories": [
        {
            "source":   "Reuters",
            "tag":      "Macro",
            "headline": "Fed Signals Extended Pause as Inflation Proves Sticky",
            "body":     "The Federal Reserve indicated it will hold rates steady through Q1 after CPI came in above expectations for the second consecutive month. Officials cited persistent services inflation as the main concern, pushing back market expectations for the next cut to mid-year.",
            "url":      "https://reuters.com",
        },
        {
            "source":   "Bloomberg",
            "tag":      "FX",
            "headline": "Peso Slips 1.2% as US Tariff Threats Resurface",
            "body":     "The MXN weakened against the dollar after the White House renewed threats of tariffs on Mexican imports tied to border policy. Analysts expect volatility to persist short-term but see limited long-term impact if negotiations resume quickly.",
            "url":      "https://bloomberg.com",
        },
        {
            "source":   "El Financiero",
            "tag":      "Mexico",
            "headline": "SHCP Projects 3.2% GDP Growth Despite External Headwinds",
            "body":     "Mexico's Finance Ministry maintained its 2026 growth forecast at 3.2%, citing strong nearshoring investment and domestic consumption as offsetting factors. The projection was met with skepticism by several independent economists.",
            "url":      "https://elfinanciero.com.mx",
        },
    ],

    "quote": {
        "text":          "Inflation is always and everywhere a monetary phenomenon in the sense that it is and can be produced only by a more rapid increase in the quantity of money than in output.",
        "attribution":   "Milton Friedman, A Monetary History of the United States, 1963",
    },
}

MOCK_WEEK_STORIES = [
    {"day": "Mon", "active": True,  "tag": "Macro",  "headline": "Fed Signals Extended Pause on Rate Cuts",        "body": "Hawkish minutes pushed rate cut expectations to mid-year. Peso hit a 3-month low on the news."},
    {"day": "Tue", "active": False, "tag": "Mexico", "headline": "SHCP Holds GDP Forecast at 3.2%",                "body": "Finance Ministry maintained its outlook despite external headwinds. Independent economists remain skeptical."},
    {"day": "Wed", "active": True,  "tag": "FX",     "headline": "US Tariff Threats Resurface, MXN Falls 1.2%",   "body": "White House renewed tariff pressure tied to border policy. Short-term volatility expected."},
    {"day": "Thu", "active": False, "tag": "Rates",  "headline": "Banxico Minutes Reveal Split on Next Move",      "body": "Two members favored a pause, three backed a 25bp cut. More uncertainty ahead for Mexican rates."},
    {"day": "Fri", "active": True,  "tag": "Trade",  "headline": "Nearshoring Investment Hits Record Q1 Pace",     "body": "New announcements in Monterrey and Saltillo pushed commitments to a record. The week's one clear bright spot."},
]

# ── Build and send ────────────────────────────

if __name__ == "__main__":
    print("Building test email...")

    # Set FRIDAY=True to also include the week-in-review section
    FRIDAY = False

    html  = build_html(
        digest       = MOCK_DIGEST,
        tickers      = MOCK_TICKERS,
        currency     = MOCK_CURRENCY,
        weather      = MOCK_WEATHER,
        week_stories = MOCK_WEEK_STORIES if FRIDAY else [],
        issue_number = 1,
        is_friday    = FRIDAY,
    )
    plain = build_plain(MOCK_DIGEST)

    send_email(html, plain)

    save_pretty_issue(
        digest       = MOCK_DIGEST,
        tickers      = MOCK_TICKERS,
        currency     = MOCK_CURRENCY,
        weather      = MOCK_WEATHER,
        week_stories = MOCK_WEEK_STORIES if FRIDAY else [],
        issue_number = 1,
        is_friday    = FRIDAY,
    )
    print("Done. Check your inbox and archive/index.html.")

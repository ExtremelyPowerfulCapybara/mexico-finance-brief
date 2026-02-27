# ─────────────────────────────────────────────
#  pretty_renderer.py  —  Full-featured HTML
#  for the web archive. Uses Google Fonts,
#  flexbox, CSS classes, and the gauge.
#  Not used for email — only for web hosting.
# ─────────────────────────────────────────────

from datetime import date, timedelta
import hashlib
from config import NEWSLETTER_NAME, NEWSLETTER_TAGLINE, AUTHOR_NAME, AUTHOR_NAMES, AUTHOR_TITLES

_seed       = int(hashlib.md5(str(date.today()).encode()).hexdigest(), 16)
AUTHOR_BYLINE_NAME  = AUTHOR_NAMES[_seed % len(AUTHOR_NAMES)]
AUTHOR_BYLINE_TITLE = AUTHOR_TITLES[(_seed // len(AUTHOR_NAMES)) % len(AUTHOR_TITLES)]
AUTHOR_BYLINE       = f"{AUTHOR_BYLINE_NAME}, {AUTHOR_BYLINE_TITLE}"

CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #dde3e8; font-family: 'DM Sans', sans-serif; padding: 40px 16px; }
  .wrap { max-width: 640px; margin: 0 auto; background: #f0f3f5; border: 1px solid #cdd4d9; }

  /* Header */
  .header { padding: 40px 48px 28px; border-bottom: 2px solid #1a1a1a; }
  .pub-label { font-size: 9px; font-weight: 500; letter-spacing: 3px; text-transform: uppercase; color: #999; margin-bottom: 10px; }
  .pub-name { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 700; color: #1a1a1a; line-height: 1.1; margin-bottom: 14px; }
  .pub-meta { display: flex; justify-content: space-between; font-size: 10px; color: #888; letter-spacing: 1px; }

  /* Ticker */
  .ticker { background: #1a1a1a; padding: 10px 48px; border-bottom: 3px solid #f0f3f5; }
  .ticker-inner { display: flex; justify-content: space-between; }
  .tick-item { text-align: center; flex: 1; padding: 6px 8px; border-left: 1px solid #2e2e2e; }
  .tick-item:first-child { border-left: none; }
  .tick-label { display: block; font-size: 8px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; color: #555; margin-bottom: 4px; }
  .tick-val { font-size: 12px; color: #d4cfc8; }
  .tick-up { color: #6abf7b; font-size: 10px; margin-left: 4px; }
  .tick-down { color: #d4695a; font-size: 10px; margin-left: 4px; }

  /* Weather */
  .weather { background: #1a1a1a; padding: 9px 48px; display: flex; gap: 20px; align-items: center; margin-top: 3px; }
  .weather-city { font-size: 11px; font-weight: 500; color: #f5f2ed; }
  .weather-temp { font-size: 11px; color: #ccc; }
  .weather-humidity { font-size: 11px; color: #ccc; }
  .weather-desc { font-size: 10px; color: #666; font-style: italic; margin-left:

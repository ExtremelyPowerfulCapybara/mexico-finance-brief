# ─────────────────────────────────────────────
#  archive.py  —  Saves pretty HTML issues
#  and regenerates the index page.
#  Output: archive/YYYY-MM-DD.html + index.html
# ─────────────────────────────────────────────

import os
import json
from datetime import date, datetime
from pretty_renderer import build_pretty_html
from config import NEWSLETTER_NAME, AUTHOR_NAME, DIGEST_DIR, ARCHIVE_DIR


def save_pretty_issue(
    digest:       dict,
    tickers:      list[dict],
    currency:     list[dict],
    weather:      dict,
    week_stories: list[dict],
    issue_number: int,
    is_friday:    bool = False,
) -> str:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    today    = date.today().isoformat()
    filename = f"{today}.html"
    filepath = os.path.join(ARCHIVE_DIR, filename)

    html = build_pretty_html(
        digest       = digest,
        tickers      = tickers,
        currency     = currency,
        weather      = weather,
        week_stories = week_stories,
        issue_number = issue_number,
        is_friday    = is_friday,
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [archive] Saved pretty issue to {filepath}")
    rebuild_index()
    return filepath


def rebuild_index() -> None:
    """
    Scans the archive folder and regenerates index.html
    with a card for each saved issue, newest first.
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    issues = sorted(
        [f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html") and f != "index.html"],
        reverse=True,
    )

    cards = ""
    for i, filename in enumerate(issues):
        issue_date_str = filename.replace(".html", "")
        try:
            dt = datetime.strptime(issue_date_str, "%Y-%m-%d")
            label = dt.strftime("%A, %B %d, %Y")
        except ValueError:
            label = issue_date_str

        issue_num = len(issues) - i
        digest_path = os.path.join(DIGEST_DIR, f"{issue_date_str}.json")
        headline    = ""
        sentiment   = ""
        if os.path.exists(digest_path):
            with open(digest_path, encoding="utf-8") as f:
                data = json.load(f)
            stories  = data.get("digest", {}).get("stories", [])
            headline = stories[0].get("headline", "") if stories else ""
            sentiment = data.get("digest", {}).get("sentiment", {}).get("label", "")

        sent_color = {"Risk-Off": "#b84a3a", "Cautious": "#9a6a1a", "Risk-On": "#4a9e6a"}.get(sentiment, "#aab4bc")
        sent_html  = f'<span style="font-size:10px; font-weight:600; letter-spacing:1px; text-transform:uppercase; color:{sent_color}; padding:3px 10px; border:1px solid {sent_color}; border-radius:20px;">{sentiment}</span>' if sentiment else ""

        cards += f"""
    <a href="{filename}" style="display:block; text-decoration:none; background:#f0f3f5; border:1px solid #cdd4d9; padding:20px 28px; margin-bottom:12px; transition:border-color 0.15s;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-family:Arial,sans-serif; font-size:9px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#aab4bc;">ISSUE #{issue_num} &middot; {label}</span>
        {sent_html}
      </div>
      <div style="font-family:Georgia,serif; font-size:17px; font-weight:700; color:#1a1a1a; line-height:1.35;">{headline or "View issue &rarr;"}</div>
    </a>"""

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NEWSLETTER_NAME} — Archive</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
  <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#dde3e8; font-family:'DM Sans',sans-serif; padding:40px 16px; }}
    .wrap {{ max-width:640px; margin:0 auto; }}
    .masthead {{ background:#1a1a1a; padding:32px 36px; margin-bottom:24px; }}
    .masthead-name {{ font-family:'Playfair Display',serif; font-size:28px; color:#f5f2ed; margin-bottom:4px; }}
    .masthead-sub {{ font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#555; }}
    a:hover div {{ color:#555 !important; }}
  </style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <div class="masthead-name">{NEWSLETTER_NAME}</div>
    <div class="masthead-sub">Archive &mdash; by {AUTHOR_NAME}</div>
  </div>
  {cards if cards else '<p style="color:#aab4bc; font-size:13px;">No issues yet.</p>'}
</div>
</body>
</html>"""

    index_path = os.path.join(ARCHIVE_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"  [archive] Index rebuilt with {len(issues)} issue(s).")

# ─────────────────────────────────────────────
#  main.py  —  Entry point
# ─────────────────────────────────────────────

import os
from fetcher        import fetch_news
from summarizer     import summarize_news
from market_data    import fetch_tickers, fetch_currency_table, fetch_weather
from storage        import save_digest, get_week_stories, is_friday
from renderer       import build_html, build_plain
from delivery       import send_email
from archive        import save_pretty_issue
from config         import DIGEST_DIR
from wordcloud_gen  import generate_wordcloud, wordcloud_as_base64
import random
from config import DIGEST_DIR, AUTHOR_NAMES, AUTHOR_TITLES


def get_issue_number() -> int:
    """Count existing digests to auto-increment issue number."""
    if not os.path.exists(DIGEST_DIR):
        return 1
    return len([f for f in os.listdir(DIGEST_DIR) if f.endswith(".json")]) + 1


def run():
    print("=" * 50)
    print("  News Digest — starting run")
    print("=" * 50)

    # ── 1. Fetch market data (fast, no LLM needed) ──
    print("\n[1/6] Fetching market data...")
    tickers  = fetch_tickers()
    currency = fetch_currency_table()
    weather  = fetch_weather()

    # ── 2. Fetch news articles ──────────────────────
    print("\n[2/6] Fetching news articles...")
    articles = fetch_news()
    if not articles:
        print("  No articles found. Check your NewsAPI key or topics.")
        return

    # ── 3. Summarize with Claude ────────────────────
    # We immediately split it into two variables for clarity.
    # digest_es is used for the email (Spanish = primary).
    # digest_en is passed to the archive for the EN/ES toggle.
    # digest (full) is saved to disk so nothing is lost.

    print(f"\n[3/6] Summarizing {len(articles)} articles with Claude...")
    digest = summarize_news(articles)
    digest_es = digest["es"]   # Spanish — primary, used in email
    digest_en = digest["en"]   # English — used in archive toggle

    # ── 4. Save digest to disk ──────────────────────
    # CHANGE: We save the full bilingual digest as-is.
    # The JSON on disk will have both "es" and "en" keys.
    # storage.py and wordcloud_gen.py read from digest["es"]
    # when they need to access stories — see those files.

    print("\n[4/6] Saving digest...")
    save_digest(digest, {"tickers": tickers, "currency": currency}, weather)
    


    # ── 5. Build and send email ─────────────────────
    print("\n[5/6] Building and sending email...")
    friday       = is_friday()
    week_stories = get_week_stories() if friday else []
    issue_num    = get_issue_number()

    # Generate word cloud on Fridays
    wordcloud_b64      = None
    wordcloud_filename = None
    if friday:
        print("  [wordcloud] Generating weekly word cloud...")
        wordcloud_b64      = wordcloud_as_base64()
        wordcloud_filename = generate_wordcloud()

    html  = build_html(
        digest         = digest_es,
        tickers        = tickers,
        currency       = currency,
        weather        = weather,
        week_stories   = week_stories,
        issue_number   = issue_num,
        is_friday      = friday,
        wordcloud_b64  = wordcloud_b64,
    )
    plain = build_plain(digest_es)

    send_email(html, plain)

    # ── 6. Save pretty HTML to archive ─────────────────
    # save_pretty_issue receives the FULL bilingual
    # digest so the archive page can render both languages
    # and wire up the EN/ES toggle button.

    print("\n[6/6] Saving to archive...")
    save_pretty_issue(
        digest             = digest,
        tickers            = tickers,
        currency           = currency,
        weather            = weather,
        week_stories       = week_stories,
        issue_number       = issue_num,
        is_friday          = friday,
        wordcloud_filename = wordcloud_filename,
    )

    print("\n" + "=" * 50)
    print(f"  Done. Issue #{issue_num} delivered.")
    if friday:
        print("  Week-in-review included.")
    print("=" * 50)


if __name__ == "__main__":
    run()

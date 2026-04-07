# ─────────────────────────────────────────────
#  telegram_bot.py  —  Post-run issue notification
#
#  Sends a Telegram message after a successful run.
#  Requires TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars.
#  Skips silently if either is missing or the request fails.
# ─────────────────────────────────────────────

import os
import requests


def send_telegram_issue_notification(
    digest: dict,
    issue_date: str,
    archive_url: str | None = None,
) -> None:
    token   = os.environ.get("TELEGRAM_TOKEN",  "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("  [telegram] TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set -- skipping.")
        return

    digest_en   = digest.get("en", digest)
    stories     = digest_en.get("stories", [])
    headline    = stories[0].get("headline", "(no headline)") if stories else "(no headline)"
    visual      = digest.get("visual", {})
    category    = visual.get("hero_category", "")
    hero_prompt = visual.get("hero_prompt", "")

    lines = [f"*The Opening Bell* — {issue_date}", ""]
    lines.append(f"*Lead:* {headline}")
    if category:
        lines.append(f"*Category:* {category}")
    if hero_prompt:
        lines.append(f"*Visual:* _{hero_prompt}_")
    if archive_url:
        lines.append("")
        lines.append(f"[Read today's issue]({archive_url})")

    text = "\n".join(lines)

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":                  chat_id,
                "text":                     text,
                "parse_mode":               "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        if resp.ok:
            print(f"  [telegram] Notification sent to chat {chat_id}.")
        else:
            print(f"  [telegram] Send failed: {resp.status_code} {resp.text[:120]}")
    except Exception as exc:
        print(f"  [telegram] Request error (non-fatal): {exc}")

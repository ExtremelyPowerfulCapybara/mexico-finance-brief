# ─────────────────────────────────────────────
#  telegram_handler.py  —  Polls Telegram for
#  hero selection callbacks and saves the chosen
#  key (opt1/opt2/opt3) into the digest JSON.
#
#  Usage (run from bot/):
#    python telegram_handler.py
#
#  Requires: TELEGRAM_TOKEN env var.
#  Offset between runs is persisted in:
#    bot/.telegram_offset
# ─────────────────────────────────────────────

import os
import json
import requests

from config import DIGEST_DIR

_OFFSET_FILE = os.path.join(os.path.dirname(__file__), ".telegram_offset")


# ── Offset persistence ────────────────────────

def _load_offset() -> int:
    if os.path.exists(_OFFSET_FILE):
        try:
            return int(open(_OFFSET_FILE).read().strip())
        except (ValueError, OSError):
            pass
    return 0


def _save_offset(offset: int) -> None:
    with open(_OFFSET_FILE, "w") as f:
        f.write(str(offset))


# ── Telegram helpers ──────────────────────────

def _answer_callback(token: str, callback_id: str, text: str = "") -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=5,
        )
    except Exception:
        pass


# ── Digest mutation ───────────────────────────

def _set_hero_selected(target_date: str, key: str) -> bool:
    """
    Write visual.hero_selected = key into the digest JSON.
    Returns True if the value was updated, False if already set or file missing.
    Does not overwrite an existing non-null value.
    """
    path = os.path.join(DIGEST_DIR, f"{target_date}.json")
    if not os.path.exists(path):
        print(f"  [telegram_handler] No digest found for {target_date} at {path}")
        return False

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    visual = data.get("visual", {})
    if visual.get("hero_selected") is not None:
        print(f"  [telegram_handler] hero_selected already set to '{visual['hero_selected']}' for {target_date} -- skipping.")
        return False

    # Validate the key is one of the generated options
    hero_options = visual.get("hero_options", {})
    if key not in hero_options:
        print(f"  [telegram_handler] Key '{key}' not found in hero_options for {target_date} -- skipping.")
        return False

    visual["hero_selected"] = key
    data["visual"] = visual

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  [telegram_handler] Set hero_selected='{key}' for {target_date}.")
    return True


# ── Main poll function ────────────────────────

def process_telegram_updates() -> None:
    """
    Poll Telegram getUpdates once, process any pending callback_query updates,
    and persist the new offset so updates are not reprocessed.
    Non-fatal on all network errors.
    """
    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token:
        print("  [telegram_handler] TELEGRAM_TOKEN not set -- skipping.")
        return

    offset = _load_offset()

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={
                "offset":          offset,
                "timeout":         5,
                "allowed_updates": json.dumps(["callback_query"]),
            },
            timeout=15,
        )
        if not resp.ok:
            print(f"  [telegram_handler] getUpdates failed: {resp.status_code} {resp.text[:120]}")
            return
        updates = resp.json().get("result", [])
    except Exception as exc:
        print(f"  [telegram_handler] Request error (non-fatal): {exc}")
        return

    new_offset = offset
    for update in updates:
        update_id  = update["update_id"]
        new_offset = update_id + 1

        cb = update.get("callback_query")
        if not cb:
            continue

        cb_id = cb["id"]
        data  = cb.get("data", "")
        parts = data.split("|")

        if len(parts) < 2:
            _answer_callback(token, cb_id)
            continue

        action     = parts[0]
        issue_date = parts[1]

        if action == "skip":
            _answer_callback(token, cb_id, "Skipped.")
            print(f"  [telegram_handler] Skip received for {issue_date}.")

        elif action == "select" and len(parts) == 3:
            key     = parts[2]
            updated = _set_hero_selected(issue_date, key)
            if updated:
                _answer_callback(token, cb_id, f"Saved: {key}")
            else:
                _answer_callback(token, cb_id, "Already set or not found.")

        else:
            _answer_callback(token, cb_id)

    _save_offset(new_offset)
    print(f"  [telegram_handler] Processed {len(updates)} update(s). Offset: {new_offset}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    process_telegram_updates()

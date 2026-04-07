# ─────────────────────────────────────────────
#  publish_site.py  --  Sync docs/ to the public web root
#
#  Called after a successful hero selection to publish the updated
#  archive to the live site.
#
#  Requires: PUBLISH_WEB_ROOT env var pointing to the destination
#  directory (e.g. /var/www/newsletter).
#
#  If PUBLISH_WEB_ROOT is not set, skips silently.
#  All errors are logged but never raised to the caller.
# ─────────────────────────────────────────────

import os
import subprocess

from config import ARCHIVE_DIR


def publish_site() -> None:
    """
    Sync ARCHIVE_DIR (docs/) to PUBLISH_WEB_ROOT using rsync.
    Skips silently if PUBLISH_WEB_ROOT is not set.
    Non-fatal on all errors.
    """
    web_root = os.environ.get("PUBLISH_WEB_ROOT", "").strip()
    if not web_root:
        print("  [publish_site] PUBLISH_WEB_ROOT not set -- skipping publish.")
        return

    # Ensure source path ends with / so rsync copies contents, not the dir itself
    src = ARCHIVE_DIR.rstrip("/") + "/"

    # Validate source exists
    if not os.path.isdir(ARCHIVE_DIR):
        print(f"  [publish_site] Source directory not found: {ARCHIVE_DIR} -- skipping publish.")
        return

    # Create destination if absent
    if not os.path.isdir(web_root):
        try:
            os.makedirs(web_root, exist_ok=True)
            print(f"  [publish_site] Created destination directory: {web_root}")
        except OSError as exc:
            print(f"  [publish_site] Could not create destination {web_root}: {exc} -- skipping publish.")
            return

    cmd = ["rsync", "-a", "--delete", src, web_root]
    print(f"  [publish_site] Syncing {src} -> {web_root}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"  [publish_site] Published successfully: {src} -> {web_root}")
            if result.stdout.strip():
                print(f"  [publish_site] rsync output: {result.stdout.strip()}")
        else:
            print(f"  [publish_site] rsync failed (exit {result.returncode}): {result.stderr.strip()}")
    except FileNotFoundError:
        print("  [publish_site] rsync not found -- skipping publish.")
    except subprocess.TimeoutExpired:
        print("  [publish_site] rsync timed out after 60s -- skipping publish.")
    except Exception as exc:
        print(f"  [publish_site] Unexpected error (non-fatal): {exc}")

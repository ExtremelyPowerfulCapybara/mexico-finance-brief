#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  scripts/rebuild_and_publish.sh
#
#  Rebuilds the archive index and publishes docs/ to the nginx web root.
#
#  Usage:
#    ./scripts/rebuild_and_publish.sh            # full rebuild + publish
#    ./scripts/rebuild_and_publish.sh --dry-run  # show what rsync would change
#
#  Run from any directory — script resolves its own paths.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Resolve project root relative to this script ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VENV="${PROJECT_ROOT}/venv"
BOT_DIR="${PROJECT_ROOT}/bot"
DOCS_DIR="${PROJECT_ROOT}/docs"
WEB_ROOT="/var/www/newsletter"

# ── Parse flags ───────────────────────────────────────────────────────────────
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        *) echo "[ERROR] Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
info()  { echo "[INFO]  $*"; }
error() { echo "[ERROR] $*" >&2; exit 1; }

# ── Preflight checks ──────────────────────────────────────────────────────────
info "Starting rebuild_and_publish..."
if [ "$DRY_RUN" = true ]; then
    info "(dry-run mode — rsync will not write anything)"
fi

[ -d "$VENV" ]    || error "Virtualenv not found at $VENV"
[ -d "$BOT_DIR" ] || error "bot/ directory not found at $BOT_DIR"
[ -d "$DOCS_DIR" ] || error "docs/ directory not found at $DOCS_DIR"

# ── Step 1: Move to project root ──────────────────────────────────────────────
info "Working from $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# ── Step 2: Activate virtualenv ───────────────────────────────────────────────
info "Activating virtualenv..."
# shellcheck source=/dev/null
source "${VENV}/bin/activate"

# ── Step 3: Rebuild archive index ─────────────────────────────────────────────
info "Rebuilding archive index..."
cd "$BOT_DIR"
python -c "import sys; sys.path.insert(0, '.'); from archive import rebuild_index; rebuild_index()"
cd "$PROJECT_ROOT"

# ── Step 4: Publish to nginx web root ─────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    info "Dry run — showing what rsync would change:"
    rsync -a --delete --dry-run --itemize-changes "${DOCS_DIR}/" "${WEB_ROOT}/"
    info "Dry run complete. No files were written."
else
    info "Publishing to nginx root (${WEB_ROOT})..."
    rsync -a --delete "${DOCS_DIR}/" "${WEB_ROOT}/"
    info "Published successfully."
fi

info "Done."

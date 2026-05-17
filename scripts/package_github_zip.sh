#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT_DIR="${1:-"$(dirname "$ROOT")/trinity_v2_github_export"}"
ZIP_PATH="${2:-"$(dirname "$ROOT")/trinity_v2_github_export.clean.zip"}"

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

command -v zip >/dev/null 2>&1 || die "zip is required"

bash "$ROOT/scripts/export_github.sh" "$EXPORT_DIR"

EXPORT_PARENT="$(cd "$(dirname "$EXPORT_DIR")" && pwd -P)"
EXPORT_BASE="$(basename "$EXPORT_DIR")"
ZIP_PARENT="$(dirname "$ZIP_PATH")"
mkdir -p "$ZIP_PARENT"
ZIP_REAL="$ZIP_PARENT/$(basename "$ZIP_PATH")"

rm -f "$ZIP_REAL"
(
  cd "$EXPORT_PARENT"
  zip -q -r -X "$ZIP_REAL" "$EXPORT_BASE" \
    -x '*/.git/*' \
    -x '*/__MACOSX/*' \
    -x '*.DS_Store' \
    -x '*/.pytest_cache/*'
)

printf 'packaged GitHub zip: %s\n' "$ZIP_REAL"

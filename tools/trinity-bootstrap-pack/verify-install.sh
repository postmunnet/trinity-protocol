#!/usr/bin/env bash
# trinity-bootstrap-pack — verify-install.sh
# Post-install sanity check: confirms a target has a valid receipt + expected files.
#
# Usage:
#   bash verify-install.sh --target <dir>

set -eu

target=""
dry_run=0
while [ $# -gt 0 ]; do
    case "$1" in
        --target) target="$2"; shift 2 ;;
        --dry-run) dry_run=1; shift ;;
        -h|--help)
            cat <<EOF
Usage: bash verify-install.sh --target <dir> [--dry-run]
Verifies the target has a .trinity-install-receipt.json with pack-v1 marker.
--dry-run is accepted for symmetry with install.sh; verify itself never writes.
EOF
            exit 0
            ;;
        *) printf 'unknown arg: %s\n' "$1" >&2; exit 2 ;;
    esac
done

if [ -z "$target" ]; then
    printf 'verify-install: --target is required\n' >&2
    exit 2
fi

receipt="$target/.trinity-install-receipt.json"
if [ ! -f "$receipt" ]; then
    printf 'verify-install: no receipt at %s\n' "$receipt" >&2
    exit 1
fi

if ! grep -q 'trinity-bootstrap-pack-v1' "$receipt"; then
    printf 'verify-install: receipt missing pack version marker\n' >&2
    exit 1
fi

printf 'verify-install: ok — %s\n' "$receipt"

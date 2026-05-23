#!/usr/bin/env bash
# trinity-bootstrap-pack — install.sh (bash entry → python core)
#
# Usage:
#   bash install.sh --target <dir> [--mode auto|greenfield|upgrade-v1|upgrade-v2]
#                   [--dry-run] [--force] [--allow-self-install]
#                   [--project-name <name>]
#
# Exit codes (passthrough from python core):
#   0  ok / dry-run
#   10 preflight failure
#   20 target unsafe / self-install refused
#   30 unknown mode
#   40 pack missing
#   50 unexpected

set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# Preflight first; abort cleanly if env is wrong.
if ! bash "$SCRIPT_DIR/preflight.sh"; then
    exit 10
fi

# Dispatch into python core. We set PYTHONPATH so `lib.installer` resolves
# regardless of where the caller's cwd is.
PYTHONPATH="$SCRIPT_DIR" exec python3 -m lib.installer "$@"

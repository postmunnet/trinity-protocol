#!/usr/bin/env bash
# trinity-bootstrap-pack — preflight.sh
# Verifies host has required tools before install.sh proceeds.
# Exit 0 on success; non-zero with clear message on miss.

set -u

err=0
log() { printf '%s\n' "$*"; }
fail() { printf 'preflight: FAIL — %s\n' "$*" >&2; err=1; }

# bash 3.2+ (macOS default). install.sh uses POSIX-ish bash; we don't depend
# on associative arrays or other 4+ features. Spec 09 §1.1 lists 4+ as
# aspirational; actual trinity_v2 kernel runs on bash 3.2 today.
if [ -z "${BASH_VERSION:-}" ]; then
    fail "this script must be run under bash"
else
    bash_major="${BASH_VERSION%%.*}"
    if [ "$bash_major" -lt 3 ]; then
        fail "bash 3+ required (found $BASH_VERSION)"
    else
        log "preflight: bash $BASH_VERSION ok"
    fi
fi

# python 3.9+ (PEP 585 generics work via `from __future__ import annotations`).
# Spec 09 §1.1 lists 3.10+ as aspirational; actual trinity_v2 kernel runs on
# python 3.9 today (1868-test suite green on 3.9.6).
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not on PATH"
else
    py_version="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null || echo 0.0)"
    py_major="${py_version%%.*}"
    py_minor="${py_version##*.}"
    if [ "$py_major" -lt 3 ] || { [ "$py_major" -eq 3 ] && [ "$py_minor" -lt 9 ]; }; then
        fail "python 3.9+ required (found $py_version)"
    else
        log "preflight: python $py_version ok"
    fi
fi

# git
if ! command -v git >/dev/null 2>&1; then
    fail "git not on PATH"
else
    log "preflight: git $(git --version 2>/dev/null | awk '{print $3}') ok"
fi

# sqlite3 (recommended; warn-only)
if ! command -v sqlite3 >/dev/null 2>&1; then
    log "preflight: sqlite3 not on PATH (warning — needed for memory-cli later)"
else
    log "preflight: sqlite3 $(sqlite3 -version 2>/dev/null | awk '{print $1}') ok"
fi

if [ "$err" -ne 0 ]; then
    log "preflight: refused — fix above and retry"
    exit 10
fi
log "preflight: ok"

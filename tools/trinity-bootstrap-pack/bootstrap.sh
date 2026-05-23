#!/usr/bin/env bash
# trinity-bootstrap-pack — bootstrap.sh
#
# Single-command Trinity install for a fresh target.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/postmunnet/trinity-protocol/main/tools/trinity-bootstrap-pack/bootstrap.sh \
#       | bash -s -- <target> [install-flags...]
#
#   # or saved + audited:
#   curl -fsSL .../bootstrap.sh > /tmp/b.sh && less /tmp/b.sh && bash /tmp/b.sh <target>
#
# Behaviour:
#   1. Clones (or `git pull`'s) trinity_v2 into $TRINITY_KERNEL_CACHE
#      (default: ~/.trinity-kernel) at the ref given by --ref (default: main).
#   2. Execs tools/trinity-bootstrap-pack/install.sh from the cache with
#      remaining args.
#
# Env:
#   TRINITY_KERNEL_CACHE — override cache location (default: ~/.trinity-kernel)
#   TRINITY_REPO_URL     — override source repo (default: GitHub canonical)
#
# Flags handled here (consumed before passing through to install.sh):
#   --ref <git-ref>           branch / tag / commit (default: main)
#   --kernel-cache <path>     override $TRINITY_KERNEL_CACHE
#   --no-update               skip `git pull` if cache exists; useful for offline runs
#
# Exit codes:
#   0  ok
#   2  bad usage
#   60 cache parent not writable
#   61 git clone / pull failed
#   *  passthrough from install.sh

set -eu

DEFAULT_REPO="https://github.com/postmunnet/trinity-protocol.git"
DEFAULT_CACHE="$HOME/.trinity-kernel"
DEFAULT_REF="main"

usage() {
    cat <<'USAGE'
Trinity bootstrap — curl|bash installer

Usage:
  curl -fsSL <repo>/raw/main/tools/trinity-bootstrap-pack/bootstrap.sh \
      | bash -s -- <target> [install-flags...]

  bash bootstrap.sh <target> [--ref <git-ref>] [--kernel-cache <path>] \
                    [--no-update] [install-flags...]

Env:
  TRINITY_KERNEL_CACHE   override cache location (default: ~/.trinity-kernel)
  TRINITY_REPO_URL       override source repo

Flags consumed here:
  --ref <git-ref>        branch/tag/commit to use (default: main)
  --kernel-cache <path>  override TRINITY_KERNEL_CACHE
  --no-update            skip `git pull` if cache exists

All remaining args are passed to install.sh.
Example:
  bash bootstrap.sh ~/code/my-app --project-name my-app
USAGE
}

if [ $# -lt 1 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    usage
    exit 0
fi

REPO_URL="${TRINITY_REPO_URL:-$DEFAULT_REPO}"
CACHE="${TRINITY_KERNEL_CACHE:-$DEFAULT_CACHE}"
REF="$DEFAULT_REF"
NO_UPDATE=0

# Parse flags this script consumes; collect the rest for install.sh
passthrough=()
while [ $# -gt 0 ]; do
    case "$1" in
        --ref)
            REF="${2:?--ref needs a value}"
            shift 2
            ;;
        --kernel-cache)
            CACHE="${2:?--kernel-cache needs a value}"
            shift 2
            ;;
        --no-update)
            NO_UPDATE=1
            shift
            ;;
        --)
            shift
            while [ $# -gt 0 ]; do passthrough+=("$1"); shift; done
            ;;
        *)
            passthrough+=("$1")
            shift
            ;;
    esac
done

# Pre-flight: cache parent must be writable.
cache_parent="$(dirname "$CACHE")"
if [ ! -d "$cache_parent" ] || [ ! -w "$cache_parent" ]; then
    printf 'bootstrap: cache parent not writable: %s\n' "$cache_parent" >&2
    exit 60
fi

# Fetch or update the cache.
if [ -d "$CACHE/.git" ]; then
    if [ "$NO_UPDATE" -eq 0 ]; then
        printf 'bootstrap: updating cache at %s (ref=%s)\n' "$CACHE" "$REF"
        (cd "$CACHE" && git fetch --quiet origin "$REF" && git checkout --quiet "$REF" && git reset --hard --quiet "origin/$REF" 2>/dev/null || git reset --hard --quiet "$REF") \
            || { printf 'bootstrap: git update failed\n' >&2; exit 61; }
    else
        printf 'bootstrap: skipping cache update (--no-update)\n'
    fi
else
    if [ -e "$CACHE" ]; then
        printf 'bootstrap: cache path exists but is not a git checkout: %s\n' "$CACHE" >&2
        exit 60
    fi
    printf 'bootstrap: cloning %s -> %s (ref=%s)\n' "$REPO_URL" "$CACHE" "$REF"
    git clone --quiet --branch "$REF" --depth 1 "$REPO_URL" "$CACHE" \
        || { printf 'bootstrap: git clone failed\n' >&2; exit 61; }
fi

# Dispatch.
install_sh="$CACHE/tools/trinity-bootstrap-pack/install.sh"
if [ ! -x "$install_sh" ]; then
    printf 'bootstrap: install.sh missing or not executable at %s\n' "$install_sh" >&2
    exit 61
fi

printf 'bootstrap: dispatching to %s\n' "$install_sh"
exec bash "$install_sh" "${passthrough[@]}"

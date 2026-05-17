"""Plan Helper — CLI entry.

Usage:
  python -m cli.agents.plan_helper draft --session-path .ai/sessions/<active>

Pipe directly into ai nnn (after operator review):
  python -m cli.agents.plan_helper draft --session-path .ai/sessions/<active> \\
      > /tmp/plan_draft.json
  # operator reviews /tmp/plan_draft.json
  bash .ai/cli/ai nnn --plan-envelope /tmp/plan_draft.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.agents.plan_helper.core import (
    ValidationError,
    draft_plan_envelope,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import LLMError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cli.agents.plan_helper",
        description=(
            "Trinity plan helper: draft plan_envelope.json from an active "
            "session's 00_CONTEXT.md + 01_PROMPT.md (post-vvv). Output JSON "
            "is shape-compatible with `ai nnn --plan-envelope`. Operator "
            "reviews/edits before submission; agent never invokes the kernel."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    draft = sub.add_parser("draft", help="draft a plan_envelope")
    draft.add_argument(
        "--session-path",
        required=True,
        help="path to the active session directory",
    )
    draft.add_argument(
        "--no-audit",
        action="store_true",
        help="skip audit emission (testing / dry-run only)",
    )
    args = parser.parse_args(argv)

    if args.cmd != "draft":
        parser.print_help()
        return 2

    repo_root = _repo_root()
    raw_session = Path(args.session_path)
    session_path = raw_session.resolve() if raw_session.is_absolute() else (repo_root / raw_session).resolve()
    if not session_path.is_dir():
        print(
            f"error: session path is not a directory: {session_path}",
            file=sys.stderr,
        )
        return 2

    audit_chain = None
    if not args.no_audit:
        events_path = repo_root / ".ai" / "audit" / "events.ndjson"
        if events_path.parent.is_dir():
            audit_chain = AuditChain(events_path)

    try:
        draft_obj = draft_plan_envelope(
            session_path=session_path,
            audit_chain=audit_chain,
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except ValidationError as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 3
    except LLMError as e:
        print(f"llm error: {e}", file=sys.stderr)
        return 4
    except Exception as e:  # noqa: BLE001
        print(f"unexpected error: {e.__class__.__name__}", file=sys.stderr)
        return 5

    print(draft_obj.to_nnn_input())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Clarification Helper — CLI entry.

Usage:
  python -m cli.agents.clarification_helper draft \\
      --session-path .ai/sessions/<active> \\
      "<operator task description>"

  echo "<description>" | python -m cli.agents.clarification_helper draft \\
      --session-path .ai/sessions/<active> -

Output JSON shape is compatible with `ai vvv --answers-file -`:
  bash .ai/cli/ai vvv --answers-file <(python -m cli.agents.clarification_helper draft ...)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.agents.clarification_helper.core import (
    ValidationError,
    draft_vvv_answers,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import LLMError


def _repo_root() -> Path:
    # cli.py: <repo>/.ai/cli/agents/clarification_helper/cli.py → 4 parents up.
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cli.agents.clarification_helper",
        description=(
            "Trinity clarification helper: draft 5 vvv answers (Goal/Scope/"
            "Constraint/Acceptance/Risk) from an operator task description "
            "and the active session's THINK/00_CONTEXT.md. Output is JSON; "
            "operator reviews/edits before piping into `ai vvv --answers-file`."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    draft = sub.add_parser("draft", help="draft 5 vvv answers")
    draft.add_argument(
        "--session-path",
        required=True,
        help="path to the active session directory (e.g. .ai/sessions/0001_...)",
    )
    draft.add_argument(
        "description",
        help="operator task description; pass '-' to read from stdin",
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

    description = args.description
    if description == "-":
        description = sys.stdin.read()
    description = description.strip()
    if not description:
        print("error: empty description", file=sys.stderr)
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
        draft_obj = draft_vvv_answers(
            description,
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

    print(draft_obj.to_vvv_args_file())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

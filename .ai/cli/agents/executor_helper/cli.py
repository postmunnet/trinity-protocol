"""Executor Helper — CLI entry.

Usage:
  python -m cli.agents.executor_helper draft \\
      --session-path .ai/sessions/<active> \\
      --step-id S1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.agents.executor_helper.core import (
    StepNotFoundError,
    ValidationError,
    draft_step_implementation,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import LLMError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cli.agents.executor_helper",
        description=(
            "Trinity executor helper: draft implementation proposal for one "
            "plan_envelope step. PROPOSAL ONLY — operator must review before "
            "any file is written or any command is executed. Agent never "
            "calls the kernel or runs commands."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    draft = sub.add_parser("draft", help="draft step implementation proposal")
    draft.add_argument("--session-path", required=True,
                       help="path to the active session directory")
    draft.add_argument("--step-id", required=True,
                       help="step id (e.g. S1) from the session's plan_envelope")
    draft.add_argument("--no-audit", action="store_true",
                       help="skip audit emission (testing only)")
    args = parser.parse_args(argv)

    if args.cmd != "draft":
        parser.print_help()
        return 2

    repo_root = _repo_root()
    raw_session = Path(args.session_path)
    session_path = raw_session.resolve() if raw_session.is_absolute() else (repo_root / raw_session).resolve()
    if not session_path.is_dir():
        print(f"error: session path not a dir: {session_path}", file=sys.stderr)
        return 2

    audit_chain = None
    if not args.no_audit:
        events_path = repo_root / ".ai" / "audit" / "events.ndjson"
        if events_path.parent.is_dir():
            audit_chain = AuditChain(events_path)

    try:
        proposal = draft_step_implementation(
            session_path=session_path,
            step_id=args.step_id,
            audit_chain=audit_chain,
        )
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except StepNotFoundError as e:
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

    print(proposal.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

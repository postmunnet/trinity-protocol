"""Retro Writer — CLI entry."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cli.agents.retro_writer.core import (
    ValidationError,
    compose_retro_lessons,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import LLMError


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cli.agents.retro_writer",
        description=(
            "Trinity retro writer: compose SEMANTIC retro layer (Lessons "
            "Learned / Patterns Observed / Doctrine Claims / Anti-Patterns) "
            "DISTINCT from rrr's mechanical T1 retro. Output is markdown to "
            "stdout — operator saves as RETRO_LESSONS.md. Agent NEVER "
            "modifies RETRO.md."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    draft = sub.add_parser("draft", help="compose semantic retro layer")
    draft.add_argument("--session-path", required=True,
                       help="path to active session dir (must contain THINK/RETRO.md)")
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
        lessons = compose_retro_lessons(
            session_path=session_path,
            repo_root=repo_root,
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
    except Exception as e:
        print(f"unexpected error: {e.__class__.__name__}", file=sys.stderr)
        return 5

    print(lessons.to_str())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Session Bootstrap Agent — CLI entry point.

Usage:
  python -m cli.agents.session_bootstrap draft "<task description>"
  echo "<task>" | python -m cli.agents.session_bootstrap draft -
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cli.agents.session_bootstrap.core import (
    ValidationError,
    propose_session,
)
from cli.core.audit import AuditChain
from cli.core.llm_call import LLMError


def _repo_root() -> Path:
    # cli.py path: <repo>/.ai/cli/agents/session_bootstrap/cli.py → 4 parents up.
    return Path(__file__).resolve().parents[4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cli.agents.session_bootstrap",
        description=(
            "Trinity session-bootstrap agent: propose slug + tier + context "
            "draft from an operator task description. Output is JSON; the "
            "operator reviews/edits/approves before running `ai session new`."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    draft = sub.add_parser("draft", help="propose a session bootstrap")
    draft.add_argument(
        "description",
        help="task description; pass '-' to read from stdin",
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
    audit_chain = None
    if not args.no_audit:
        events_path = repo_root / ".ai" / "audit" / "events.ndjson"
        if events_path.parent.is_dir():
            audit_chain = AuditChain(events_path)

    try:
        proposal = propose_session(
            description,
            repo_root=repo_root,
            audit_chain=audit_chain,
        )
    except ValidationError as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 3
    except LLMError as e:
        print(f"llm error: {e}", file=sys.stderr)
        return 4
    except Exception as e:  # noqa: BLE001
        # Last-resort guard so we never leak unredacted traces; redaction
        # already applied inside llm_call layer for LLM errors.
        print(f"unexpected error: {e.__class__.__name__}", file=sys.stderr)
        return 5

    print(json.dumps(proposal.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

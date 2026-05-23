"""ai vvv — Verify understanding (5 questions).

Spec ref: .ai/shims/vvv/SHIM.md (canonical contract)
          docs/specs/04_GRAPH_SPEC.md (decided_by enforcement)

Required: an active session (set by `ai session new`).

If graph_state is unset (READY default), this command auto-fires the `sss`
trigger (decided_by: kernel) to enter THINK before presenting the 5
questions. Answers are then captured (via flags / file / interactive),
written to `THINK/01_PROMPT.md`, and a `.state/vvv_pass` marker is created.
Two audit events are appended: `vvv.proposed` (kernel) and `vvv.passed`
(human).
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.audit import get_chain_for_project
from ..core.loop import Loop
from ..core.next_action import compute as compute_next, render_one_line
from ..core.recordproxy import capture
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
)
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tools_registry import call as call_tool

app = typer.Typer()
console = Console()


QUESTIONS = [
    ("Goal", "What does success look like? (one sentence)"),
    ("Scope", "What is explicitly in scope? What is out?"),
    ("Constraint", "What cannot be touched? (policies, boundary docs)"),
    ("Acceptance", "What measurable signal proves 'done'?"),
    ("Risk", "What is the most likely failure mode?"),
]


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    answer: List[str] = typer.Option(
        None, "--answer", help="N=text (repeatable, e.g. --answer 1=...)"
    ),
    answers_file: Optional[Path] = typer.Option(
        None,
        "--answers-file",
        help='JSON or YAML file with answers (e.g. {"1":"...","2":"..."} '
        'or `1: "..."` per line). Format auto-detected.',
    ),
    show: bool = typer.Option(
        False, "--show", help="Print 5 questions and exit (no writes)"
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport. When present, kernel "
        "verifies HMAC before running vvv; on failure emits "
        "vvv.hmac_rejected and exits 79.",
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        help="(KI-2026-05-16-001) Explicit session id or path — bypasses the "
        "global current_session pointer. Pair with sss output to avoid "
        "routing drift under concurrent ritual invocation.",
    ),
):
    """Run vvv ritual: 5 questions, write THINK/01_PROMPT.md + vvv_pass."""
    if ctx.invoked_subcommand is not None:
        return
    _run(answer or [], answers_file, show, hmac_envelope_file, session)


def _run(
    answer_flags: List[str],
    answers_file: Optional[Path],
    show_only: bool,
    hmac_envelope_file: Optional[Path] = None,
    session_override: Optional[str] = None,
) -> None:
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)

    if show_only:
        _print_questions()
        return

    if hmac_envelope_file is not None:
        from ..core.audit import get_chain_for_project
        from ..core.hmac_gate import enforce_hmac_or_exit
        chain = get_chain_for_project(config.project_root)
        enforce_hmac_or_exit(
            hmac_envelope_file=hmac_envelope_file,
            chain=chain,
            ritual="vvv",
            session_id=session_path.name,
        )

    # Part 2 (capture wiring): open a RecordProxy capture for the entire
    # vvv invocation. The contextvar set inside capture() flows into
    # AuditChain.append (via emit_via_proxy), so every audit event below
    # is stamped with this capture's capture_id automatically.
    with capture(
        session_path,
        ritual="vvv",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("answer_flags.json", {"flags": answer_flags})
        if answers_file is not None:
            cap.input("answers_file_path.txt", str(answers_file))

        _run_inner(answer_flags, answers_file, config, session_path, cap)


def _run_inner(
    answer_flags: List[str],
    answers_file: Optional[Path],
    config,
    session_path: Path,
    cap,
) -> None:
    # Load the vvv ritual pack up-front so the missing-answers branch can
    # emit pack-declared vvv.failed before exiting (RC v1.1-rc Article XII.5).
    # Resolve rituals_root from project_root (not cwd) so the loader survives
    # tests that chdir to a tmp project.
    vvv_pack = load_pack(
        "vvv",
        rituals_root=config.project_root / ".ai" / "rituals",
    )

    answers = _parse_answers(answer_flags, answers_file)
    missing = [i for i in range(1, 6) if not answers.get(i, "").strip()]
    if missing:
        _print_questions()
        console.print(
            f"[yellow]Missing answers for Q{missing}. Provide via "
            f"--answer N=text (repeatable) or --answers-file <path> "
            f'(JSON `{{"1":"..."}}` or YAML `1: "..."`).[/yellow]'
        )
        # Emit pack-declared vvv.failed before exiting (Article IX —
        # evidence trail for failed proposals).
        get_chain_for_project(config.project_root).append(
            "vvv.failed",
            {
                "session_id": session_path.name,
                "decided_by": "kernel",
                "reason": "missing_answers",
                "missing": missing,
            },
        )
        raise typer.Exit(2)

    loop = Loop(
        session_path,
        graph_name="standard",
        project_root=config.project_root,
    )

    if loop.current() == "READY":
        # Delegate to the sss ritual library so the .ai/rituals/sss/ pack is
        # honored (RC v1.1-rc Article XII.5). Same single canonical site used
        # by `ai session new` — see commands/sss.py for the integration shape.
        from .sss import fire_sss_transition
        fire_sss_transition(
            loop,
            session_id=session_path.name,
            decided_by="kernel",
            evidence={"task": session_path.name},
        )

    # Article XX guard — pack must accept the (current, next) pair BEFORE
    # any vvv-side state mutation (audit append, prompt write, marker touch).
    assert_transition_allowed(vvv_pack, loop.current(), "THINK")

    loop.chain.append(
        "vvv.invoked",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "kernel",
        },
    )

    loop.chain.append(
        "vvv.proposed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "kernel",
            "questions_count": 5,
        },
    )

    prompt_path = session_path / "THINK" / "01_PROMPT.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_md = _render_prompt_md(answers, session_path.name)
    prompt_path.write_text(prompt_md, encoding="utf-8")
    cap.output("01_PROMPT.md", prompt_md)

    # Phase 2.3 — surface past incidents from the Knowledge Brain.
    # Best-effort: a memory-cli failure does not block vvv. Hits are
    # informational warnings; the human still decides whether to
    # proceed.
    past_hits = _query_past_incidents(config.project_root, answers)
    _print_past_incidents(past_hits)

    marker = session_path / ".state" / "vvv_pass"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    cap.validation("vvv_pass.marker", "1")

    loop.chain.append(
        "vvv.passed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "human",
            "marker_path": str(marker.relative_to(config.project_root)),
        },
    )

    console.print(
        Panel(
            f"vvv passed.\n"
            f"  prompt: {prompt_path.relative_to(config.project_root)}\n"
            f"  marker: {marker.relative_to(config.project_root)}\n"
            f"  graph_state: {loop.current()}",
            title="✅ vvv",
            border_style="green",
        )
    )
    # Layer 5a — next-action footer
    console.print(
        render_one_line(
            compute_next(
                config.project_root,
                session_path=session_path,
                graph_state=loop.current(),
            )
        )
    )


def _resolve_session(config) -> Path:
    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if not cur:
        console.print(
            "[red]No active session. Run `ai session new <task>` first.[/red]"
        )
        raise typer.Exit(2)
    p = Path(cur)
    if not p.exists():
        console.print(f"[red]Session path missing: {p}[/red]")
        raise typer.Exit(2)
    return p


def _resolve_with_override(config, session_override: Optional[str]) -> Path:
    """KI-2026-05-16-001 fix — resolve session with optional --session override.

    When session_override is provided, bypass the global current_session
    pointer (which drifts under concurrent ritual invocation) and resolve
    explicitly via session_resolver. Emit a `kernel.session_override` audit
    row when the explicit path differs from current_session so audit
    consumers can correlate the override to the drift incident.
    """
    if not session_override:
        return _resolve_session(config)

    from ..core.session_resolver import (
        SessionNotFoundError,
        resolve_explicit_session,
    )
    try:
        explicit = resolve_explicit_session(config.project_root, session_override)
    except SessionNotFoundError as exc:
        console.print(
            f"[red]session not found: {session_override}[/red]\n"
            f"  searched: {[str(c) for c in exc.candidates]}"
        )
        raise typer.Exit(2)

    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if cur and Path(cur).resolve() != explicit.resolve():
        get_chain_for_project(config.project_root).append(
            "kernel.session_override",
            {
                "ritual": "vvv",
                "explicit_session": str(explicit),
                "current_session": str(cur),
                "decided_by": "kernel",
                "reason": "KI-2026-05-16-001 routing drift bypass",
            },
        )
        console.print(
            f"[yellow]⚠ --session={session_override} overrides current_session "
            f"({Path(cur).name}) → using explicit session {explicit.name}[/yellow]"
        )
    return explicit


def _print_questions() -> None:
    body = "\n\n".join(
        f"[bold cyan]Q{i + 1} ({cat})[/bold cyan]\n  {q}"
        for i, (cat, q) in enumerate(QUESTIONS)
    )
    console.print(
        Panel(body, title="🔍 vvv — 5 questions", border_style="cyan")
    )


def _parse_answers(
    answer_flags: List[str], answers_file: Optional[Path]
) -> Dict[int, str]:
    answers: Dict[int, str] = {}
    if answers_file:
        data = _load_answers_file(answers_file)
        for k, v in data.items():
            answers[int(k)] = str(v)
    for flag in answer_flags:
        if "=" not in flag:
            console.print(
                f"[red]bad --answer (need N=text): {flag!r}[/red]"
            )
            raise typer.Exit(2)
        k, v = flag.split("=", 1)
        answers[int(k)] = v
    return answers


def _load_answers_file(path: Path) -> Dict:
    """Load Q-answers map from a JSON or YAML file.

    Tries JSON first (cheapest, backwards-compatible with prior callers);
    falls back to yaml.safe_load on JSONDecodeError. Emits a clear error
    that mentions both formats if neither parses.
    """
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as json_err:
        try:
            import yaml  # PyYAML is a kernel runtime dep (see .ai/requirements.txt)

            loaded = yaml.safe_load(raw)
        except Exception as yaml_err:
            console.print(
                f"[red]--answers-file {path}: neither valid JSON nor YAML.[/red]\n"
                f"  JSON error: {json_err}\n"
                f"  YAML error: {yaml_err}\n"
                f'  Expected: JSON `{{"1":"...","2":"..."}}` or YAML `1: "..."`.'
            )
            raise typer.Exit(2)
        if not isinstance(loaded, dict):
            console.print(
                f"[red]--answers-file {path}: YAML root must be a mapping "
                f'(got {type(loaded).__name__}). Expected `1: "..."`.[/red]'
            )
            raise typer.Exit(2)
        return loaded


def _query_past_incidents(
    project_root: Path, answers: Dict[int, str]
) -> List[Dict]:
    """Build an FTS query from the Q1/Q4 answers and surface up to 3
    past retros that match. Best-effort — silent when memory-cli is
    unavailable."""
    # Goal (Q1) is the most semantically rich; acceptance (Q4) often
    # contains the symptom keywords.
    parts = [answers.get(1, ""), answers.get(4, "")]
    query = " ".join(p.strip() for p in parts if p.strip())
    if not query:
        return []
    inv = call_tool(
        project_root,
        "memory-cli",
        f"search {json.dumps(query)} --limit=3",
        timeout_seconds=10,
    )
    if not inv.ok or not inv.envelope:
        return []
    data = inv.envelope.get("data") or {}
    return data.get("results") or []


def _print_past_incidents(hits: List[Dict]) -> None:
    if not hits:
        return
    body = []
    for h in hits:
        title = h.get("title") or h.get("id")
        when = h.get("created_at") or "?"
        snippet = (h.get("snippet") or "").replace("\n", " ")
        body.append(
            f"[bold]{title}[/bold]  [dim]{when}[/dim]\n"
            f"  id: {h.get('id')}\n"
            f"  {snippet}"
        )
    console.print(
        Panel(
            "\n\n".join(body),
            title=f"⚠️  {len(hits)} past incident(s) match this goal",
            border_style="yellow",
        )
    )


def _render_prompt_md(answers: Dict[int, str], session_id: str) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        f"session: {session_id}",
        "ritual: vvv",
        "status: passed",
        f"last-updated: {today}",
        "---",
        "",
        "# `vvv` — 5 Questions",
        "",
    ]
    for i, (cat, q) in enumerate(QUESTIONS, start=1):
        lines += [
            f"## Q{i} — {cat}",
            "",
            f"**Question:** {q}",
            "",
            f"**Answer:** {answers[i]}",
            "",
        ]
    return "\n".join(lines)

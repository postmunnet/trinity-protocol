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
from ..core import artifact_version
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
    amend: bool = typer.Option(
        False,
        "--amend",
        help="Amend the goal contract in-session (creates goal_contract.v(N+1), "
        "never mutates v1). Pair with --answer N=... + --reason. Amended "
        "answers reset to agent_draft/unconfirmed.",
    ),
    confirm: Optional[str] = typer.Option(
        None,
        "--confirm",
        help="Mark selected questions human-confirmed, e.g. --confirm 1,2,4. "
        "Creates a new goal_contract version (answer_source is contract state).",
    ),
    history: bool = typer.Option(
        False,
        "--history",
        help="Print goal_contract version history + amendment records "
        "(read-only).",
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Reason for --amend (required when amending)."
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
    if history:
        _run_history(session)
        return
    if confirm is not None:
        _run_confirm(confirm, session)
        return
    if amend:
        _run_amend(answer or [], answers_file, reason, session)
        return
    _run(answer or [], answers_file, show, hmac_envelope_file, session)


def _run(
    answer_flags: List[str],
    answers_file: Optional[Path],
    show_only: bool,
    hmac_envelope_file: Optional[Path] = None,
    session_override: Optional[str] = None,
) -> None:
    # Prompt mode (--show) is pure static text — the 5 questions never
    # depend on SSOT or an active session. Check it BEFORE loading config
    # so adapters can render the questions from any cwd, with no session
    # open, and without an audit side effect (two-phase adapter contract,
    # 2026-06-12). Submission below still requires both.
    if show_only:
        _print_questions()
        return

    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)

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

    # Q24.10 step 2 — materialise the goal contract as a versioned, machine-
    # readable artifact (v1) the first time vvv passes. answer_source defaults
    # are conservative: every answer is agent_draft / human_confirmed:false
    # until an explicit `vvv --confirm`. Idempotent: a re-run that finds v1
    # already present refreshes 01_PROMPT.md only (never mutates v1).
    if not (session_path / ".state" / "goal_contract.v1.json").exists():
        contract = _build_goal_contract(answers, session_path.name, version=1)
        artifact_version.write_version(session_path, "goal_contract", contract, 1)
        (session_path / "THINK" / "01_PROMPT.v1.md").write_text(
            prompt_md, encoding="utf-8"
        )
        _write_goal_signal(session_path)
        cap.output("goal_contract.v1.json", contract)

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

    # Fire vvv_pass: THINK → SANDBOX (verifier-decided; evidence = the
    # just-written marker). Guarded so a re-run on an already-transitioned
    # session re-writes 01_PROMPT.md / refreshes the marker without crashing
    # on a non-existent SANDBOX-state transition.
    if loop.current() == "THINK":
        loop.fire(
            "vvv_pass",
            decided_by="verifier",
            evidence={
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
    # Thin wrapper over the shared canonical resolver (consolidates the
    # 6 former duplicates; the shared one also rejects the sessions
    # container so a drifted current_session pointer cannot leak the root).
    from ..core.session_resolver import resolve_current_session

    return resolve_current_session(config)


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


# ───────────────────── Q24.10 step 2: goal-contract versioning ─────────────────────
# vvv is the SEMANTIC owner here; artifact_version.py is the storage layer.

def _build_goal_contract(
    answers: Dict[int, str], session_id: str, version: int
) -> Dict:
    """Structured goal contract with per-question answer_source.

    Conservative default: every answer is agent_draft / human_confirmed:false
    (the kernel cannot know whether a human typed --answer or an agent drafted
    it, so it must assume unconfirmed until an explicit --confirm).
    """
    questions = {}
    for i, (cat, _q) in enumerate(QUESTIONS, start=1):
        questions[f"q{i}"] = {
            "category": cat,
            "answer": answers.get(i, ""),
            "answered_by": "agent_draft",
            "human_confirmed": False,
            "confirmed_at": None,
        }
    return {"session": session_id, "version": version, "questions": questions}


def _unconfirmed_questions(contract: Dict) -> List[str]:
    """Return question ids whose answer is not human-confirmed."""
    return [
        qid
        for qid, q in (contract.get("questions") or {}).items()
        if not q.get("human_confirmed")
    ]


def _write_goal_signal(session_path: Path) -> Dict:
    """Materialise the machine-readable unconfirmed-answer signal in .state.

    This is the source of truth step 3 / aaa / rrr will consume — they must
    NOT have to regex markdown to know whether the goal is fully confirmed.
    """
    contract = artifact_version.resolve_latest(session_path, "goal_contract")
    unconfirmed = _unconfirmed_questions(contract)
    signal = {
        "goal_contract_version": artifact_version.active_version(
            session_path, "goal_contract"
        ),
        "has_unconfirmed_answers": bool(unconfirmed),
        "unconfirmed_questions": unconfirmed,
    }
    (session_path / ".state" / "goal_contract_signal.json").write_text(
        json.dumps(signal, indent=2), encoding="utf-8"
    )
    return signal


def _parse_question_ids(spec: str) -> List[str]:
    """Parse '1,2,4' or 'q1,q2' → ['q1','q2','q4']."""
    out = []
    for tok in spec.replace(" ", "").split(","):
        if not tok:
            continue
        tok = tok if tok.startswith("q") else f"q{tok}"
        out.append(tok)
    return out


def _run_confirm(confirm_spec: str, session_override: Optional[str]) -> None:
    """ai vvv --confirm 1,2 — mark selected questions human-confirmed.

    Confirmation is part of the contract state, so it produces a new
    immutable version (v1 is never mutated).
    """
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)
    chain = get_chain_for_project(config.project_root)

    try:
        base = artifact_version.resolve_latest(session_path, "goal_contract")
    except FileNotFoundError:
        console.print("[red]No goal contract yet — run `ai vvv` first.[/red]")
        raise typer.Exit(2)

    ids = _parse_question_ids(confirm_spec)
    valid = set(base.get("questions") or {})
    bad = [q for q in ids if q not in valid]
    if bad:
        console.print(f"[red]unknown question(s): {bad} (have {sorted(valid)})[/red]")
        raise typer.Exit(2)

    from_v = artifact_version.active_version(session_path, "goal_contract")
    to_v = from_v + 1
    new = json.loads(json.dumps(base))  # deep copy
    new["version"] = to_v
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for q in ids:
        new["questions"][q]["answered_by"] = "human"
        new["questions"][q]["human_confirmed"] = True
        new["questions"][q]["confirmed_at"] = now

    artifact_version.write_version(session_path, "goal_contract", new, to_v)
    artifact_version.write_amendment_record(
        session_path, "goal_contract", from_v, to_v,
        f"confirm {','.join(ids)}", [f"confirm_{q}" for q in ids],
    )
    signal = _write_goal_signal(session_path)
    chain.append("goal_contract_amended", {
        "session_id": session_path.name, "from_version": from_v,
        "to_version": to_v, "changes": [f"confirm_{q}" for q in ids],
        "decided_by": "human",
    })
    chain.append("active_goal_contract_changed", {
        "session_id": session_path.name, "active_version": to_v,
        "has_unconfirmed_answers": signal["has_unconfirmed_answers"],
        "decided_by": "kernel",
    })
    console.print(Panel(
        f"confirmed {', '.join(ids)} (goal_contract v{from_v} → v{to_v})\n"
        f"  has_unconfirmed_answers: {signal['has_unconfirmed_answers']}\n"
        f"  unconfirmed: {signal['unconfirmed_questions'] or '—'}",
        title="✅ vvv --confirm", border_style="green",
    ))


def _run_amend(
    answer_flags: List[str],
    answers_file: Optional[Path],
    reason: Optional[str],
    session_override: Optional[str],
) -> None:
    """ai vvv --amend --answer N=... --reason ... — amend the goal contract.

    vvv owns goal authority, so a goal-level change here is LEGAL (unlike
    nnn --amend which rejects it). Amended answers reset to agent_draft /
    unconfirmed. Creates goal_contract.v(N+1); v1 stays immutable.
    """
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)
    chain = get_chain_for_project(config.project_root)

    reason = (reason or "").strip()
    if not reason:
        console.print("[red]--amend requires --reason.[/red]")
        raise typer.Exit(2)

    changes = _parse_answers(answer_flags, answers_file)
    changes = {i: v for i, v in changes.items() if v.strip()}
    if not changes:
        console.print(
            "[red]--amend requires at least one --answer N=text to change.[/red]"
        )
        raise typer.Exit(2)

    try:
        base = artifact_version.resolve_latest(session_path, "goal_contract")
    except FileNotFoundError:
        console.print("[red]No goal contract to amend — run `ai vvv` first.[/red]")
        raise typer.Exit(2)

    from_v = artifact_version.active_version(session_path, "goal_contract")
    to_v = from_v + 1
    changed_questions = [f"q{i}" for i in sorted(changes)]

    chain.append("goal_amend_proposed", {
        "session_id": session_path.name, "from_version": from_v,
        "reason": reason, "changed_questions": changed_questions,
        "decided_by": "kernel",
    })

    new = json.loads(json.dumps(base))  # deep copy
    new["version"] = to_v
    for i, text in changes.items():
        qid = f"q{i}"
        # amended answers revert to unconfirmed (must be re-confirmed)
        new["questions"][qid]["answer"] = text
        new["questions"][qid]["answered_by"] = "agent_draft"
        new["questions"][qid]["human_confirmed"] = False
        new["questions"][qid]["confirmed_at"] = None

    artifact_version.write_version(session_path, "goal_contract", new, to_v)
    rfile, _rec = artifact_version.write_amendment_record(
        session_path, "goal_contract", from_v, to_v, reason, changed_questions,
    )
    # refresh 01_PROMPT.md latest view (historical 01_PROMPT.v1.md untouched)
    answers_for_md = {
        i: new["questions"][f"q{i}"]["answer"] for i in range(1, 6)
    }
    (session_path / "THINK" / "01_PROMPT.md").write_text(
        _render_prompt_md(answers_for_md, session_path.name), encoding="utf-8"
    )
    signal = _write_goal_signal(session_path)
    chain.append("goal_contract_amended", {
        "session_id": session_path.name, "from_version": from_v,
        "to_version": to_v, "reason": reason, "changes": changed_questions,
        "decided_by": "kernel",
    })
    chain.append("active_goal_contract_changed", {
        "session_id": session_path.name, "active_version": to_v,
        "has_unconfirmed_answers": signal["has_unconfirmed_answers"],
        "decided_by": "kernel",
    })
    console.print(Panel(
        f"goal contract amended v{from_v} → v{to_v}\n"
        f"  changed: {', '.join(changed_questions)}\n"
        f"  reason: {reason}\n"
        f"  has_unconfirmed_answers: {signal['has_unconfirmed_answers']} "
        f"{signal['unconfirmed_questions']}\n"
        f"  record: {rfile.relative_to(config.project_root)}",
        title="✅ vvv --amend", border_style="green",
    ))


def _run_history(session_override: Optional[str]) -> None:
    """ai vvv --history — goal_contract version history (read-only)."""
    from rich.table import Table

    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)

    versions = artifact_version.list_versions(session_path, "goal_contract")
    if not versions:
        console.print("[yellow]no goal contract yet — run `ai vvv` first.[/yellow]")
        return
    active = artifact_version.active_version(session_path, "goal_contract")
    records = {
        r["to_version"]: r
        for r in artifact_version.list_amendment_records(session_path, "goal_contract")
    }
    table = Table(show_header=True, header_style="cyan", title="goal_contract history")
    table.add_column("version")
    table.add_column("origin")
    table.add_column("changes")
    table.add_column("reason")
    for v in versions:
        rec = records.get(v)
        origin = f"amended from v{rec['from_version']}" if rec else "initial vvv"
        changes = ", ".join(rec.get("changes", [])) if rec else "—"
        reason = (rec.get("reason", "") if rec else "—") or "—"
        marker = " ◀ active" if v == active else ""
        table.add_row(f"v{v}{marker}", origin, changes, reason)
    console.print(table)


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

"""ai nnn — Numbered plan + budget check.

Spec ref: .ai/shims/nnn/SHIM.md (canonical contract)
          docs/specs/03_GOAL_LOOP_SPEC.md §8 (Budget enforcement)
          Decision D11 (budget breach -> NEEDS_HUMAN)

Required: an active session in graph_state SANDBOX with .state/vvv_pass present
(vvv must have transitioned THINK→SANDBOX before nnn runs — see RITUALS.md
canonical order: sss → vvv → nnn → gogogo → ddd → rrr → close).

A plan envelope JSON file (--plan-envelope path) supplies the numbered
steps + budget estimates. The command:

  1. Validates the .state/vvv_pass marker
  2. Runs Budget.check against the envelope
  3. On breach without override: writes 02_SCOPE.md with budget_status
     NEEDS_HUMAN, no .state/nnn_pass, no SANDBOX->DO firing
  4. On pass (or override): writes 02_SCOPE.md, 03_ACCEPTANCE.md,
     .state/plan.json, .state/nnn_pass marker, then fires nnn_pass
     (SANDBOX->DO, kernel). vvv already fired vvv_pass (THINK->SANDBOX)
     as part of the prior vvv ritual, so nnn fires a single transition.

Two audit events are appended in either path: nnn.proposed (kernel) and
on-pass nnn.passed (human or kernel-via-override).
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.audit import get_chain_for_project
from ..core.budget import Budget
from ..core.loop import Loop
from ..core.next_action import compute as compute_next, render_one_line
from ..core import plan_version
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
)
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tools_registry import call as call_tool

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    plan_envelope: Optional[Path] = typer.Option(
        None, "--plan-envelope", help="Path to JSON plan envelope file"
    ),
    amend: bool = typer.Option(
        False,
        "--amend",
        help="Amend the current session's plan in-place (creates plan.v(N+1), "
        "never mutates v1). Requires --plan-envelope <delta> with a `reason`.",
    ),
    history: bool = typer.Option(
        False,
        "--history",
        help="Print the plan version history + amendment records for the "
        "current session. Read-only.",
    ),
    scope_md: Optional[Path] = typer.Option(
        None, "--scope-md", help="Optional pre-rendered SCOPE markdown"
    ),
    acceptance_md: Optional[Path] = typer.Option(
        None,
        "--acceptance-md",
        help="Optional pre-rendered ACCEPTANCE markdown",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport. When present, kernel "
        "verifies HMAC before running nnn; on failure emits "
        "nnn.hmac_rejected and exits 79.",
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        help="(KI-2026-05-16-001) Explicit session id or path — bypasses "
        "the global current_session pointer to avoid routing drift.",
    ),
):
    """Run nnn ritual: budget-check the envelope, write SCOPE/ACCEPTANCE/plan."""
    if ctx.invoked_subcommand is not None:
        return
    if history:
        _run_history(session)
        return
    if amend:
        if plan_envelope is None:
            console.print(
                "[red]--amend requires --plan-envelope <delta.json> "
                "(must contain a `reason`).[/red]"
            )
            raise typer.Exit(2)
        _run_amend(plan_envelope, session)
        return
    if plan_envelope is None:
        console.print(
            "[red]Missing --plan-envelope <path>. (or use --amend / --history)[/red]"
        )
        raise typer.Exit(2)
    _run(plan_envelope, scope_md, acceptance_md, hmac_envelope_file, session)


def _run(
    envelope_path: Path,
    scope_md_path: Optional[Path],
    acceptance_md_path: Optional[Path],
    hmac_envelope_file: Optional[Path] = None,
    session_override: Optional[str] = None,
) -> None:
    from ..core.recordproxy import capture
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
            ritual="nnn",
            session_id=session_path.name,
        )

    vvv_marker = session_path / ".state" / "vvv_pass"
    if not vvv_marker.exists():
        console.print(
            "[red]Missing .state/vvv_pass — run `ai vvv` first.[/red]"
        )
        raise typer.Exit(2)

    # Part 2 (capture wiring): one capture per nnn invocation.
    with capture(
        session_path,
        ritual="nnn",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("invocation_params.json", {
            "envelope_path": str(envelope_path),
            "scope_md_path": str(scope_md_path) if scope_md_path else None,
            "acceptance_md_path": str(acceptance_md_path) if acceptance_md_path else None,
        })
        _nnn_inner(envelope_path, scope_md_path, acceptance_md_path, config, session_path, cap)


def _nnn_inner(
    envelope_path: Path,
    scope_md_path: Optional[Path],
    acceptance_md_path: Optional[Path],
    config,
    session_path: Path,
    cap,
) -> None:

    # R7 — resolve a relative --plan-envelope against project_root
    # (not cwd). Users typically invoke `ai nnn` from a sub-directory
    # of the workspace; treating the path as cwd-relative made the
    # ergonomic path (e.g. `--plan-envelope plan.json`) silently
    # fail. Absolute paths are passed through unchanged.
    if not envelope_path.is_absolute():
        candidate = (config.project_root / envelope_path).resolve()
        if not envelope_path.exists() and candidate.exists():
            envelope_path = candidate

    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    cap.input("plan_envelope.json", envelope)

    loop = Loop(
        session_path,
        graph_name="standard",
        project_root=config.project_root,
    )

    # RC v1.1-rc Article XII.5 — load the nnn pack and assert its declared
    # transition envelope BEFORE any state mutation (Article XX). Note the
    # pack's allowed_next_states is the CONCEPTUAL successor ("PLAN"); the
    # physical state machine collapses PLAN into DO (graphs/standard.yaml
    # fires nnn_pass: SANDBOX→DO). The pack guard asserts the conceptual
    # envelope; the loop.fire below asserts the physical envelope.
    nnn_pack = load_pack(
        "nnn",
        rituals_root=config.project_root / ".ai" / "rituals",
    )
    assert_transition_allowed(nnn_pack, loop.current(), "PLAN")

    loop.chain.append(
        "nnn.invoked",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "kernel",
            "envelope_path": str(envelope_path),
        },
    )

    # P8 Phase 3 — verification_contract gate per spec §4.6.1.
    # When THINK/verification_contract.json is present, validate it
    # (schema via validate_contract_dict, semantic via
    # verifier_runtime.precedence_validator) BEFORE budget check. On
    # violation: emit nnn.proposed with rejection_reason +
    # offending acceptance id, then Exit(1). When the file is absent,
    # nnn behaves identically to before (backward-compat — current
    # sessions don't yet produce this artifact).
    contract_path = session_path / "THINK" / "verification_contract.json"
    if contract_path.is_file():
        try:
            contract_dict = json.loads(contract_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            loop.chain.append(
                "nnn.proposed",
                {
                    "session_id": session_path.name,
                    "graph_state": loop.current(),
                    "decided_by": "kernel",
                    "rejection_reason": "contract_unreadable",
                    "detail": str(exc),
                },
            )
            console.print(
                f"[red]verification_contract.json unreadable: {exc}[/red]"
            )
            raise typer.Exit(1)

        # Schema validation (§4.6.1 + schema additionalProperties:false)
        try:
            from ..core.verification_contract import validate_contract_dict
            validate_contract_dict(contract_dict)
        except Exception as schema_exc:
            loop.chain.append(
                "nnn.proposed",
                {
                    "session_id": session_path.name,
                    "graph_state": loop.current(),
                    "decided_by": "kernel",
                    "rejection_reason": "schema_invalid",
                    "detail": str(schema_exc)[:500],
                },
            )
            console.print(
                f"[red]verification_contract schema invalid: {schema_exc}[/red]"
            )
            raise typer.Exit(1)

        # Semantic precedence validation (§4.6.1)
        from ..core.verifier_runtime import precedence_validator
        rules_doc = None
        rules_path = config.project_root / ".ai" / "policies" / "verifier-rules.yaml"
        if rules_path.is_file():
            try:
                import yaml as _yaml
                rules_doc = _yaml.safe_load(rules_path.read_text(encoding="utf-8"))
            except Exception:
                rules_doc = None
        violations = precedence_validator(contract_dict, rules_doc=rules_doc)
        if violations:
            # spec §4.6.1: rejection_reason + offending acceptance id
            offending_id = None
            for v in violations:
                # Heuristic: pull the first quoted acceptance id from the message
                import re as _re
                m = _re.search(r"acceptance ['\"]([^'\"]+)['\"]", v)
                if m:
                    offending_id = m.group(1)
                    break
            loop.chain.append(
                "nnn.proposed",
                {
                    "session_id": session_path.name,
                    "graph_state": loop.current(),
                    "decided_by": "kernel",
                    "rejection_reason": "precedence_violation",
                    "acceptance_id": offending_id,
                    "violations": violations[:10],  # cap payload size
                },
            )
            console.print(
                f"[red]verification_contract precedence violation(s): "
                f"{len(violations)} found, first: {violations[0]}[/red]"
            )
            raise typer.Exit(1)

    budget = Budget.for_project(config.project_root)
    verdict = budget.check(envelope, graph_name="standard")

    # plan.budget_checked — pack-declared event, emit immediately after
    # the budget verdict is known so audit downstream can reason about it.
    loop.chain.append(
        "plan.budget_checked",
        {
            "session_id": session_path.name,
            "decided_by": "kernel",
            "budget_ok": verdict.ok,
            "breaches": verdict.breaches,
            "overrides_applied": verdict.overrides_applied,
        },
    )

    loop.chain.append(
        "nnn.proposed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "kernel",
            "plan_steps": len(envelope.get("steps", [])),
            "estimated_duration_min": envelope.get(
                "estimated_duration_minutes"
            ),
            "budget_ok": verdict.ok,
            "breaches": verdict.breaches,
            "overrides_applied": verdict.overrides_applied,
        },
    )

    if not verdict.ok:
        # Pack-declared nnn.failed — emit before exiting so empirical
        # ratification (Article XII.5) has evidence the budget-breach branch
        # honors the pack's audit event set.
        loop.chain.append(
            "nnn.failed",
            {
                "session_id": session_path.name,
                "graph_state": loop.current(),
                "decided_by": "kernel",
                "reason": "budget_breach",
                "breaches": verdict.breaches,
            },
        )
        scope_path = session_path / "THINK" / "02_SCOPE.md"
        scope_path.parent.mkdir(parents=True, exist_ok=True)
        scope_path.write_text(
            _render_needs_human_scope(envelope, verdict),
            encoding="utf-8",
        )
        console.print(
            Panel(
                f"NEEDS_HUMAN — budget breach.\n"
                f"  scope: {scope_path.relative_to(config.project_root)}\n"
                f"  breaches: {verdict.breaches}\n\n"
                f"Revise estimates or add a budget_override "
                f"(decided_by: human, reason: ...) to plan envelope.",
                title="🟡 nnn — NEEDS_HUMAN",
                border_style="yellow",
            )
        )
        raise typer.Exit(0)

    # Phase 2.3 — Knowledge Brain hints. Best-effort: if memory-cli is
    # unreachable, hints=[] and the default render keeps working.
    memory_hints = _query_memory_hints(config.project_root, envelope)
    _print_memory_hints(memory_hints)

    scope_text = (
        scope_md_path.read_text(encoding="utf-8")
        if scope_md_path and scope_md_path.exists()
        else _render_default_scope(envelope, verdict, memory_hints)
    )
    acceptance_text = (
        acceptance_md_path.read_text(encoding="utf-8")
        if acceptance_md_path and acceptance_md_path.exists()
        else _render_default_acceptance(envelope)
    )

    (session_path / "THINK" / "02_SCOPE.md").write_text(
        scope_text, encoding="utf-8"
    )
    cap.output("02_SCOPE.md", scope_text)
    (session_path / "THINK" / "03_ACCEPTANCE.md").write_text(
        acceptance_text, encoding="utf-8"
    )
    cap.output("03_ACCEPTANCE.md", acceptance_text)

    # R11 — write executable acceptance YAML if envelope provides it.
    # Envelope shape: { "acceptance": [ { id, command, expect_*, ... }, ... ] }
    if isinstance(envelope.get("acceptance"), list):
        import yaml as _yaml

        yaml_doc = {
            "session": session_path.name,
            "ritual": "rrr-input",
            "acceptance": envelope["acceptance"],
        }
        (session_path / "THINK" / "03_ACCEPTANCE.yaml").write_text(
            _yaml.safe_dump(yaml_doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    plan_state_path = session_path / ".state" / "plan.json"
    plan_state_path.parent.mkdir(parents=True, exist_ok=True)
    envelope_with_meta = {
        **envelope,
        "approved_by": "human" if verdict.overrides_applied else "kernel",
        "approved_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "budget_status": (
            "human_override_approved"
            if verdict.overrides_applied
            else "within_default"
        ),
    }
    # Initial nnn lands as plan.v1 (immutable) + active snapshot plan.json.
    # write_plan_version writes plan.v1.json, plan.json (snapshot) and
    # plan_meta.json so `nnn --amend` and gogogo's resolver have a baseline.
    plan_version.write_plan_version(session_path, envelope_with_meta, 1)
    cap.output("plan.json", envelope_with_meta)

    nnn_marker = session_path / ".state" / "nnn_pass"
    nnn_marker.touch()
    cap.validation("nnn_pass.marker", "1")

    loop.chain.append(
        "nnn.passed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "human" if verdict.overrides_applied else "kernel",
            "plan_path": str(plan_state_path.relative_to(config.project_root)),
            "overrides_applied": verdict.overrides_applied,
        },
    )

    # SANDBOX -> DO (kernel, trigger=nnn_pass). Per RITUALS.md canonical order,
    # vvv fires THINK→SANDBOX upon answering the 5 questions; nnn fires the
    # second physical transition SANDBOX→DO. nnn no longer double-fires.
    loop.fire(
        "nnn_pass",
        decided_by="kernel",
        evidence={
            "plan_path": str(
                plan_state_path.relative_to(config.project_root)
            )
        },
    )

    console.print(
        Panel(
            f"nnn passed.\n"
            f"  scope: THINK/02_SCOPE.md\n"
            f"  acceptance: THINK/03_ACCEPTANCE.md\n"
            f"  plan: .state/plan.json\n"
            f"  marker: .state/nnn_pass\n"
            f"  graph_state: {loop.current()}",
            title="✅ nnn",
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

    See vvv._resolve_with_override for the design notes; same semantics.
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
                "ritual": "nnn",
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


def _run_amend(delta_path: Path, session_override: Optional[str]) -> None:
    """ai nnn --amend — create plan.v(N+1) from a delta envelope.

    Q24.10 invariants: v1 immutable · new version always · reason required ·
    goal-level change rejected (→ vvv --amend) · audit plan_amended.
    """
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)
    chain = get_chain_for_project(config.project_root)

    # resolve the delta path (R7 ergonomics: relative → project_root)
    if not delta_path.is_absolute():
        candidate = (config.project_root / delta_path).resolve()
        if not delta_path.exists() and candidate.exists():
            delta_path = candidate
    delta = json.loads(delta_path.read_text(encoding="utf-8"))

    reason = (delta.get("reason") or "").strip()
    if not reason:
        console.print(
            "[red]amend delta must contain a non-empty `reason`.[/red]"
        )
        raise typer.Exit(2)

    try:
        base = plan_version.resolve_active_plan(session_path)
    except FileNotFoundError:
        console.print(
            "[red]No existing plan to amend — run `ai nnn --plan-envelope` "
            "first.[/red]"
        )
        raise typer.Exit(2)

    # Invariant #4 — goal-level change is out of scope for nnn --amend.
    if plan_version.is_goal_level_change(base, delta):
        chain.append(
            "plan_amend_rejected",
            {
                "session_id": session_path.name,
                "reason": "goal-level change requires vvv --amend",
                "recommended_next": "ai vvv --amend",
                "decided_by": "kernel",
            },
        )
        console.print(
            "[red]amend rejected — goal-level change detected.[/red]\n"
            "  the goal contract is owned by vvv, not nnn.\n"
            "👉 next: ai vvv --amend"
        )
        raise typer.Exit(3)

    from_version = plan_version.active_version(session_path)
    to_version = from_version + 1

    # New full version = delta, keeping the original goal (goal unchanged here).
    new_plan = dict(delta)
    new_plan["goal"] = base.get("goal")
    new_plan["amended_from"] = from_version
    new_plan["amended_at"] = plan_version._now()
    new_plan.pop("reason", None)  # reason lives in the amendment record

    changes = plan_version.diff_changes(base, new_plan)
    plan_version.write_plan_version(session_path, new_plan, to_version)
    rfile, record = plan_version.write_amendment_record(
        session_path, from_version, to_version, reason, changes
    )

    # Refresh executable acceptance YAML so rrr sees the amended gates.
    if isinstance(new_plan.get("acceptance"), list):
        import yaml as _yaml

        (session_path / "THINK" / "03_ACCEPTANCE.yaml").write_text(
            _yaml.safe_dump(
                {
                    "session": session_path.name,
                    "ritual": "rrr-input",
                    "acceptance": new_plan["acceptance"],
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    # Human-readable delta under THINK/AMENDMENTS/.
    adir = session_path / "THINK" / "AMENDMENTS"
    adir.mkdir(parents=True, exist_ok=True)
    (adir / f"{record['seq']:04d}_PLAN_DELTA.md").write_text(
        f"# Plan amendment {record['seq']:04d}\n\n"
        f"- from version: v{from_version}\n"
        f"- to version: v{to_version}\n"
        f"- changes: {', '.join(changes)}\n\n"
        f"## Reason\n\n{reason}\n",
        encoding="utf-8",
    )

    chain.append(
        "plan_amended",
        {
            "session_id": session_path.name,
            "from_version": from_version,
            "to_version": to_version,
            "reason": reason,
            "changes": changes,
            "decided_by": "kernel",
            "requires_human": False,
        },
    )

    console.print(
        Panel(
            f"plan amended v{from_version} → v{to_version}.\n"
            f"  changes: {', '.join(changes)}\n"
            f"  reason: {reason}\n"
            f"  active: .state/plan.v{to_version}.json\n"
            f"  record: {rfile.relative_to(config.project_root)}",
            title="✅ nnn --amend",
            border_style="green",
        )
    )


def _run_history(session_override: Optional[str]) -> None:
    """ai nnn --history — print plan versions + amendment records (read-only)."""
    from rich.table import Table

    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)

    versions = plan_version.list_plan_versions(session_path)
    active = plan_version.active_version(session_path)
    records = {r["to_version"]: r for r in plan_version.list_amendment_records(session_path)}

    if not versions:
        console.print("[yellow]no plan versions yet — run `ai nnn` first.[/yellow]")
        return

    table = Table(show_header=True, header_style="cyan", title="plan version history")
    table.add_column("version")
    table.add_column("origin")
    table.add_column("changes")
    table.add_column("reason")
    for v in versions:
        rec = records.get(v)
        if rec:
            origin = f"amended from v{rec['from_version']}"
            changes = ", ".join(rec.get("changes", []))
            reason = rec.get("reason", "")
        else:
            origin = "initial nnn"
            changes = "—"
            reason = "—"
        marker = " ◀ active" if v == active else ""
        table.add_row(f"v{v}{marker}", origin, changes, reason)
    console.print(table)


def _render_needs_human_scope(
    envelope: Dict[str, Any], verdict
) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        "ritual: nnn",
        "status: needs_human",
        "budget_status: NEEDS_HUMAN",
        f"last-updated: {today}",
        "---",
        "",
        "# `nnn` — Plan rejected by budget check (D11)",
        "",
        "## Breaches",
        "",
    ]
    for b in verdict.breaches:
        lines.append(
            f"- **{b['cap']}** — estimate {b['estimate']} > limit "
            f"{b['limit']} (×{b['ratio']})"
        )
    lines += [
        "",
        "## Resolution paths",
        "",
        "- Reduce estimates (split plan into multiple sessions)",
        "- Add `budget_override` to the plan envelope with "
        "`decided_by: human` and an explicit `reason`",
        "",
        "## Plan envelope (rejected)",
        "",
        "```json",
        json.dumps(envelope, indent=2, ensure_ascii=False),
        "```",
        "",
    ]
    return "\n".join(lines)


def _render_default_scope(
    envelope: Dict[str, Any], verdict, memory_hints=None
) -> str:
    today = datetime.date.today().isoformat()
    status = (
        "human_override" if verdict.overrides_applied else "passed"
    )
    lines = [
        "---",
        "ritual: nnn",
        f"status: {status}",
        f"budget_status: {status}",
        f"last-updated: {today}",
        "---",
        "",
        "# `nnn` — Plan",
        "",
    ]
    for s in envelope.get("steps", []):
        lines.append(
            f"### Step {s.get('n', '?')} — {s.get('title', '?')}"
        )
        lines += [
            "",
            f"- **Estimate:** {s.get('estimate_min', '?')} min",
            f"- **Risk:** {s.get('risk', 'unknown')}",
            f"- **Spec ref:** {s.get('spec_ref', '-')}",
            "",
        ]
    if verdict.overrides_applied:
        lines += ["## Budget override (decided_by: human)", ""]
        for o in verdict.overrides_applied:
            lines.append(
                f"- {o['cap']}: default={o['default_limit']} "
                f"override={o['override_limit']} "
                f"reason={o.get('reason', '')!r}"
            )
        lines.append("")
    if memory_hints:
        lines += [
            "## Memory hints (similar past sessions)",
            "",
            "_Auto-pulled by `nnn` from memory-cli search; informational only._",
            "",
        ]
        for h in memory_hints:
            title = h.get("title") or h.get("id")
            when = h.get("created_at") or "?"
            lines.append(
                f"- **{title}** _{when}_ "
                f"(`{h.get('id')}`) — {(h.get('snippet') or '').strip()}"
            )
        lines.append("")
    return "\n".join(lines)


def _query_memory_hints(
    project_root: Path, envelope: Dict[str, Any]
) -> list:
    """Compose a query from envelope.goal + step titles, search the
    Brain, return up to 3 hits. Best-effort: empty list on any failure
    (tool missing, parse error, no results)."""
    parts = []
    if isinstance(envelope.get("goal"), str):
        parts.append(envelope["goal"])
    for s in envelope.get("steps", []) or []:
        title = s.get("title")
        if isinstance(title, str):
            parts.append(title)
    query = " ".join(p.strip() for p in parts if p and p.strip())
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


def _print_memory_hints(hits: list) -> None:
    if not hits:
        return
    body = []
    for h in hits:
        title = h.get("title") or h.get("id")
        when = h.get("created_at") or "?"
        body.append(
            f"[bold]{title}[/bold]  [dim]{when}[/dim]\n"
            f"  id: {h.get('id')}"
        )
    console.print(
        Panel(
            "\n\n".join(body),
            title=f"💡 {len(hits)} memory hint(s) for this plan",
            border_style="cyan",
        )
    )


def _render_default_acceptance(envelope: Dict[str, Any]) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        "ritual: nnn",
        "status: passed",
        f"last-updated: {today}",
        "---",
        "",
        "# Acceptance Criteria",
        "",
        "All steps in `02_SCOPE.md` complete with verifier PASS;",
        "audit chain validates after every transition.",
        "",
    ]
    return "\n".join(lines)

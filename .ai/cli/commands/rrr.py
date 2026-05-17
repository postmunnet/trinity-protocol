"""ai rrr — Retrospective + machine-enforced terminal gate.

Spec ref: .ai/shims/rrr/SHIM.md (canonical contract)
          docs/migration/08_PHASE2_MEMORY_CLI_ALPHA.md (R9 + R10 + R11
          locked decisions: write both retro files, executable
          acceptance, kill the RRR contract: PARTIAL pattern)

Pipeline:

  1. resolve session; assert graph_state in {VERIFIED, PROMOTED,
     DEPLOYED, RETRO}
  2. (optional --auto-deploy) advance VERIFIED -> PROMOTED -> DEPLOYED
     using decided_by=human (explicit user opt-in via flag); skip for
     non-deploy sessions where the user wants to record the rrr
     directly. NOT a substitute for `ai ddd` (Phase 5 proper) — this
     flag is a dev-only convenience for kernel/scaffold sessions.
  3. parse THINK/03_ACCEPTANCE.yaml (if present) and run each command
     via core.acceptance.run_all
  4. run core.forbidden_diff.check against HEAD baseline
  5. compute core.metrics.metrics_for_session from the audit chain
  6. write THINK/RETRO.md (R9 part 1; lives with the capsule)
  7. write .ai/memory/retros/<seq>_<date>_<HH>_<MM>_<ampm>_<type>-<slug>.md
     (R9 part 2; canonical memory copy)
  8. if --dry-run: stop here, exit 0 (gate green) or 1 (any required
     failure)
  9. else: fire DEPLOYED -> RETRO (kernel) if needed, index the
     memory retro, append rrr.completed, fire RETRO -> DONE (kernel).
     COLD-tier memory index failure blocks RETRO -> DONE visibly.

Exits non-zero if any required acceptance command fails OR forbidden
diff has violations OR (in non-dry-run) any state mutation fails.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.acceptance import (
    AcceptanceReport,
    load_acceptance,
    run_all,
)
from ..core.audit import AuditChain, get_chain_for_project
from ..core.auth import load_hmac_envelope, verify_hmac
from ..core.forbidden_diff import ForbiddenDiffReport, check as check_forbidden
from ..core.loop import Loop
from ..core.metrics import SessionMetrics, metrics_for_session
from ..core.next_action import compute as compute_next, render_one_line
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
)
from ..core.session_archive import archive_session
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tools_registry import ToolInvocation, call as call_tool

app = typer.Typer()
console = Console()


VALID_RRR_STATES = {"VERIFIED", "PROMOTED", "DEPLOYED", "RETRO"}
HMAC_REJECT_EXIT = 79


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run gate + write retros; do NOT fire RETRO->DONE"
    ),
    auto_deploy: bool = typer.Option(
        False,
        "--auto-deploy",
        help="(deprecated as of Phase 5; use `ai ddd` then `ai rrr` instead) advance VERIFIED->PROMOTED->DEPLOYED via human-decided fires before running rrr",
    ),
    retro_type: str = typer.Option(
        "feat", "--type", help="Memory retro type slug (feat/fix/ops/...)"
    ),
    baseline: str = typer.Option(
        "HEAD", "--baseline", help="Forbidden-diff baseline ref (default HEAD; R13)"
    ),
    retroactive: bool = typer.Option(
        False,
        "--retroactive",
        help="(R14) Stitch a past session into the audit chain — skips graph_state guard and does NOT fire RETRO->DONE; pairs with --session",
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        help="Session id or path to operate on (overrides current_session; required with --retroactive)",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport (e.g. trinity-tg-bot) "
        "carrying {session,command,args,ts,nonce[,user_id],sig}. When present, "
        "kernel verifies HMAC via core.auth.verify_hmac before running the "
        "retro pipeline; on failure emits rrr.hmac_rejected and exits 79. "
        "Spec 14 §6.1 Layer 3 / Decision Y / R35.",
    ),
    with_lessons: bool = typer.Option(
        False,
        "--with-lessons",
        help="After the deterministic retro envelope is written, invoke the "
        "retro_writer agent to draft a SEMANTIC retro layer (Lessons Learned, "
        "Patterns Observed, Doctrine Claims, Anti-Patterns). The agent's "
        "output is saved to THINK/RETRO_LESSONS.md. Fail-soft: rrr completes "
        "normally if the agent fails or times out. Skipped under --dry-run "
        "and --retroactive.",
    ),
):
    """Run the rrr terminal gate."""
    if ctx.invoked_subcommand is not None:
        return
    code = _run(
        dry_run=dry_run,
        auto_deploy=auto_deploy,
        retro_type=retro_type,
        baseline=baseline,
        retroactive=retroactive,
        session_override=session,
        hmac_envelope_file=hmac_envelope_file,
        with_lessons=with_lessons,
    )
    raise typer.Exit(code=code)


def _run(
    dry_run: bool,
    auto_deploy: bool,
    retro_type: str,
    baseline: str = "HEAD",
    retroactive: bool = False,
    session_override: Optional[str] = None,
    hmac_envelope_file: Optional[Path] = None,
    with_lessons: bool = False,
) -> int:
    from ..core.recordproxy import capture
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    project_root = config.project_root
    if retroactive and not session_override:
        console.print(
            "[red]--retroactive requires --session <id-or-path>[/red]"
        )
        return 2
    session_path = (
        _resolve_explicit_session(project_root, session_override)
        if session_override
        else _resolve_session(config)
    )
    sid = session_path.name

    # Part 2 (capture wiring): one capture per rrr invocation.
    with capture(
        session_path,
        ritual="rrr",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("invocation_params.json", {
            "dry_run": dry_run,
            "auto_deploy": auto_deploy,
            "retro_type": retro_type,
            "baseline": baseline,
            "retroactive": retroactive,
            "session_override": session_override,
            "hmac_envelope_file": str(hmac_envelope_file) if hmac_envelope_file else None,
            "with_lessons": with_lessons,
        })
        return _rrr_inner(
            dry_run=dry_run,
            auto_deploy=auto_deploy,
            retro_type=retro_type,
            baseline=baseline,
            retroactive=retroactive,
            session_override=session_override,
            hmac_envelope_file=hmac_envelope_file,
            with_lessons=with_lessons,
            config=config,
            project_root=project_root,
            session_path=session_path,
            sid=sid,
            cap=cap,
        )


def _invoke_retro_writer(session_path: Path, project_root: Path) -> Optional[Path]:
    """Subprocess-invoke retro_writer agent and write stdout to RETRO_LESSONS.md.

    Returns the written path on success, None on any failure (fail-soft).
    The agent NEVER modifies RETRO.md (its own contract); we save its
    markdown output as RETRO_LESSONS.md alongside.
    """
    import subprocess as _sub
    try:
        proc = _sub.run(
            [
                "bash",
                str(project_root / ".ai" / "cli" / "agent"),
                "retro_writer",
                "draft",
                "--session-path",
                str(session_path),
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            console.print(
                f"[yellow]⚠ retro_writer agent failed "
                f"(exit={proc.returncode}); skipping lessons[/yellow]"
            )
            return None
        target = session_path / "THINK" / "RETRO_LESSONS.md"
        target.write_text(proc.stdout, encoding="utf-8")
        console.print(f"   [dim]semantic retro: {target.name}[/dim]")
        return target
    except Exception as exc:
        console.print(
            f"[yellow]⚠ retro_writer invocation failed: {exc}[/yellow]"
        )
        return None


def _rrr_inner(
    *,
    dry_run: bool,
    auto_deploy: bool,
    retro_type: str,
    baseline: str,
    retroactive: bool,
    session_override: Optional[str],
    hmac_envelope_file: Optional[Path],
    with_lessons: bool,
    config,
    project_root,
    session_path,
    sid: str,
    cap,
) -> int:

    loop = Loop(session_path, graph_name="standard", project_root=project_root)
    cur = loop.current()
    if not retroactive and cur not in VALID_RRR_STATES:
        console.print(
            f"[red]graph_state must be in {sorted(VALID_RRR_STATES)}; "
            f"got {cur!r}. Run `ai next` to see the right next step "
            f"(usually: `ai gogogo` then `ai ddd`).[/red]"
        )
        return 2

    # RC v1.1-rc Article XII.5 — load the rrr pack so the empirical
    # ratification trail anchors the audit-event vocabulary. The pack
    # declares CONCEPTUAL states (DEPLOY/RETRO → RETRO/DONE); the physical
    # graph admits VERIFIED/PROMOTED/DEPLOYED/RETRO as legal current states.
    # Pre-existing pack/graph naming drift — out of scope for this session.
    rrr_pack = load_pack(
        "rrr",
        rituals_root=project_root / ".ai" / "rituals",
    )

    # Emit pack-declared rrr.invoked first, before HMAC verify or any state
    # mutation — gives reviewers a single entry-point event per invocation.
    get_chain_for_project(project_root).append(
        "rrr.invoked",
        {
            "session_id": sid,
            "graph_state": cur,
            "decided_by": "kernel",
            "retroactive": retroactive,
            "dry_run": dry_run,
            "auto_deploy": auto_deploy,
        },
    )

    # R35: HMAC verify before any audit append / state mutation. Reject
    # path leaves graph_state untouched and emits rrr.hmac_rejected.
    transition_evidence_extra = {}
    if hmac_envelope_file is not None:
        chain = get_chain_for_project(project_root)
        try:
            envelope, payload_bytes, sig, ts_iso = load_hmac_envelope(
                hmac_envelope_file
            )
        except (ValueError, json.JSONDecodeError, OSError) as e:
            chain.append(
                "rrr.hmac_rejected",
                {
                    "session_id": sid,
                    "reason": "bad_envelope",
                    "ts_iso": None,
                    "detail": str(e),
                },
            )
            console.print(f"[red]rrr.hmac_rejected: bad_envelope ({e})[/red]")
            return HMAC_REJECT_EXIT

        ok, hmac_reason = verify_hmac(payload_bytes, sig, ts_iso)
        if not ok:
            chain.append(
                "rrr.hmac_rejected",
                {
                    "session_id": sid,
                    "reason": hmac_reason,
                    "ts_iso": ts_iso,
                    "envelope_keys": sorted(list(envelope.keys())),
                },
            )
            console.print(f"[red]rrr.hmac_rejected: {hmac_reason}[/red]")
            return HMAC_REJECT_EXIT

        transition_evidence_extra = {
            "via": "tg-bot:hmac",
            "hmac_ts": ts_iso,
            "hmac_nonce": envelope.get("nonce"),
            "hmac_user_id": envelope.get("user_id"),
        }

    if auto_deploy and cur == "VERIFIED":
        cur = loop.fire(
            "promote_request",
            decided_by="human",
            evidence={"reason": "ai rrr --auto-deploy convenience"},
        )
    if auto_deploy and cur == "PROMOTED":
        cur = loop.fire(
            "deploy_request",
            decided_by="human",
            evidence={"reason": "ai rrr --auto-deploy convenience"},
        )

    # 3. acceptance gate
    acceptance_yaml = session_path / "THINK" / "03_ACCEPTANCE.yaml"
    acc_report: Optional[AcceptanceReport] = None
    if acceptance_yaml.exists():
        items = load_acceptance(acceptance_yaml)
        acc_report = run_all(items, cwd=project_root)
        acc_report.yaml_path = acceptance_yaml
        _print_acceptance(acc_report)
    else:
        console.print(
            f"[yellow]No THINK/03_ACCEPTANCE.yaml — acceptance gate "
            f"SKIPPED (R11 not yet authored for this session).[/yellow]"
        )

    # 4. forbidden diff (R13 — baseline configurable; Phase 0.5 — honour
    #    plan_envelope.allowed_paths as carve-outs when the operator's
    #    plan explicitly authorised writes inside a D1 zone).
    # 2026-05-14 — also load <session>/.state/baseline_untracked.json
    # (written by `ai sss`) and forward to check_forbidden so a parallel
    # HOLD session's pre-existing untracked files are not flagged as this
    # session's violations (feedback_rrr_cross_session_forbidden_diff).
    plan_allowed_paths = _load_plan_envelope_allowed_paths(session_path)
    baseline_untracked_path = session_path / ".state" / "baseline_untracked.json"
    if baseline_untracked_path.is_file():
        try:
            baseline_untracked = json.loads(
                baseline_untracked_path.read_text(encoding="utf-8")
            )
            if not isinstance(baseline_untracked, list):
                baseline_untracked = []
        except (json.JSONDecodeError, OSError):
            baseline_untracked = []
    else:
        # Backward compat: sessions created before the sss snapshot landed
        # have no file; default to [] which gives identical-to-before behavior.
        baseline_untracked = []
    fd_report = check_forbidden(
        project_root,
        baseline=baseline,
        allowed_paths=plan_allowed_paths,
        baseline_untracked=baseline_untracked,
    )
    _print_forbidden_diff(fd_report)

    # 5. metrics
    metrics = metrics_for_session(loop.chain, sid)
    _print_metrics(metrics)

    # 6 + 7. write retros
    # Dry-run writes ONLY the session-local copy. The canonical memory
    # retro is the artifact of a real run that fires RETRO -> DONE; if
    # we minted it on dry-run, every preview would pollute the memory
    # index with stale duplicates.
    retro_md_text = _render_retro(metrics, acc_report, fd_report, sid)
    session_retro = session_path / "THINK" / "RETRO.md"
    session_retro.parent.mkdir(parents=True, exist_ok=True)
    session_retro.write_text(retro_md_text, encoding="utf-8")
    cap.output("RETRO.md", retro_md_text)

    # Phase 12 §3 + §4 — also write the deterministic closure envelope
    # (retro_envelope.md). Additive only: RETRO.md production above is
    # unchanged. The envelope holds mechanical-only fields per §3.1; no
    # semantic prose (Article IX). See TRINITY_RETRO_RRR_SPLIT_SPEC_V1.
    envelope_tier_for_render = _load_plan_envelope_tier(session_path)
    retro_envelope_text = _render_retro_envelope(
        session_path=session_path,
        project_root=project_root,
        sid=sid,
        metrics=metrics,
        acc_report=acc_report,
        fd_report=fd_report,
        baseline=baseline,
        tier=envelope_tier_for_render,
        graph_state_final=loop.current(),
        chain=loop.chain,
    )
    session_retro_envelope = session_path / "THINK" / "retro_envelope.md"
    session_retro_envelope.write_text(retro_envelope_text, encoding="utf-8")
    cap.output("retro_envelope.md", retro_envelope_text)

    cap.validation("acceptance_report.json", {
        "ok": acc_report.ok if acc_report else None,
        "items": [
            {
                "id": r.item.id,
                "passed": r.passed,
                "required": r.item.required,
                "description": r.item.description,
                "exit_code": r.exit_code,
            }
            for r in (acc_report.items if acc_report else [])
        ],
    })
    cap.validation("forbidden_diff_report.json", {
        "violations": [str(v) for v in fd_report.violations],
        "baseline": baseline,
    })

    memory_retro_path: Optional[Path] = None
    if not dry_run:
        memory_retro_path = _memory_retro_path(project_root, retro_type, sid)
        memory_retro_path.parent.mkdir(parents=True, exist_ok=True)
        memory_retro_path.write_text(retro_md_text, encoding="utf-8")

    # Wire — semantic retro layer via retro_writer agent (opt-in flag).
    # Warm-path only: skip under --dry-run and --retroactive so the agent
    # only runs when the operator has committed to closing the loop.
    if with_lessons and not dry_run and not retroactive:
        _invoke_retro_writer(session_path, project_root)

    console.print(f"\n[bold]wrote[/bold]\n  {session_retro.relative_to(project_root)}")
    if memory_retro_path:
        console.print(f"  {memory_retro_path.relative_to(project_root)}")

    # gate verdict
    gate_failures = []
    if acc_report and not acc_report.ok:
        gate_failures.append(
            f"{len(acc_report.required_failures)} acceptance required-failures"
        )
    if not fd_report.ok:
        gate_failures.append(
            f"{len(fd_report.violations)} forbidden-path writes"
        )

    if dry_run:
        if gate_failures:
            console.print(
                Panel(
                    "[red]DRY-RUN gate: FAIL[/red]\n  " + "\n  ".join(gate_failures),
                    title="🟡 ai rrr",
                    border_style="red",
                )
            )
            return 1
        console.print(
            Panel(
                "[green]DRY-RUN gate: PASS[/green]\n  retros written; "
                "RETRO->DONE NOT fired (--dry-run).",
                title="🟢 ai rrr (dry-run)",
                border_style="green",
            )
        )
        return 0

    if gate_failures:
        console.print(
            Panel(
                "[red]gate FAIL — refusing to fire RETRO->DONE[/red]\n  "
                + "\n  ".join(gate_failures)
                + "\n\nRe-run with --dry-run after fixing failures.",
                title="🔴 ai rrr",
                border_style="red",
            )
        )
        return 1

    # 9. finalize: fire DEPLOYED->RETRO if needed, append rrr.completed,
    # fire RETRO->DONE. R14 retroactive mode skips state mutation entirely
    # — the goal is to stitch a *past* session into the audit chain
    # without changing the kernel's current_session or graph_state.
    if not retroactive and loop.current() == "DEPLOYED":
        loop.fire(
            "rrr",
            decided_by="kernel",
            evidence={"by": "ai rrr", **transition_evidence_extra},
        )

    # memory_retro_path is guaranteed set in non-dry-run path above
    assert memory_retro_path is not None

    # 9.5. delegate retro indexing to memory-cli (Article IX — Memory
    # retrieves evidence; it does not derive semantic truth). Replaces
    # the legacy Phase 2.2 semantic-feed path. The retro file is the
    # source of truth; memory-cli makes it *findable*, never transforms it.
    tier = _load_plan_envelope_tier(session_path)
    memory_index = _index_memory_cli(project_root, memory_retro_path)
    _print_memory_index(memory_index, tier=tier)

    # T4 delegation audit (every rrr→organ delegation MUST be auditable;
    # Article XIX — delegation without audit = hidden orchestration).
    artifact_sha256 = _sha256_of_file(memory_retro_path)
    delegation_ok = _memory_index_ok(memory_index)
    loop.chain.append(
        "rrr.delegated_call",
        {
            "session_id": sid,
            "tool": "memory-cli",
            "action": "index",
            "target": str(memory_retro_path.relative_to(project_root)),
            "result": "PASS" if delegation_ok else "FAIL",
            "artifact_sha256": artifact_sha256,
            "workflow_id": sid,
        },
    )

    # T3 severity-by-tier: HOT → warning only; WARM → FAILED_VISIBLE but
    # gate still passes (best-effort); COLD → blocks RETRO→DONE by being
    # recorded as a required-failure in the acceptance pile. We surface
    # the severity in the print + audit payload so operators see it.
    index_severity = _index_severity_for_tier(tier, delegation_ok)
    if _memory_index_blocks_completion(index_severity, retroactive=retroactive):
        memory_index_summary = _summarize_memory_index(memory_index)
        loop.chain.append(
            "ritual.transition.blocked",
            {
                "session_id": sid,
                "ritual": "rrr",
                "trigger": "rrr_complete",
                "graph_state": loop.current(),
                "to_state": "DONE",
                "decided_by": "kernel",
                "reason": "memory_index_failed_cold_tier",
                "tier": tier,
                "memory_retro": str(
                    memory_retro_path.relative_to(project_root)
                ),
                "memory_index": memory_index_summary,
                "memory_index_severity": index_severity,
            },
        )
        console.print(
            Panel(
                "[red]memory-cli index failed for COLD tier - refusing "
                "RETRO->DONE[/red]\n"
                f"  retro: {memory_retro_path.relative_to(project_root)}\n"
                f"  error: {memory_index_summary.get('error', '<unknown>')}",
                title="🔴 ai rrr",
                border_style="red",
            )
        )
        console.print(
            render_one_line(
                compute_next(
                    project_root,
                    session_path=session_path,
                    graph_state=loop.current(),
                )
            )
        )
        return 1

    loop.chain.append(
        "rrr.completed" if not retroactive else "rrr.retroactive",
        {
            "session_id": sid,
            "graph_state": loop.current(),
            "decided_by": "kernel",
            "retroactive": retroactive,
            "memory_retro": str(
                memory_retro_path.relative_to(project_root)
            ),
            "session_retro": str(session_retro.relative_to(project_root)),
            "acceptance_total": (
                len(acc_report.items) if acc_report else 0
            ),
            "acceptance_passed": (
                sum(1 for r in acc_report.items if r.passed)
                if acc_report
                else 0
            ),
            "forbidden_diff_violations": len(fd_report.violations),
            "metrics_event_count": metrics.event_count,
            "tier": tier,
            "memory_index": _summarize_memory_index(memory_index),
            "memory_index_severity": index_severity,
        },
    )

    # Suggest-pin (T1 + closing principle 2: Memory pinning confers
    # authority; rrr may suggest, never auto-pin). Surface ONLY when the
    # session has a decided_by:human transition (i.e. a real human
    # decision happened — ddd approve/promote/deploy).
    _maybe_suggest_pin(loop.chain, sid, memory_retro_path, project_root)

    if not retroactive:
        loop.fire(
            "rrr_complete",
            decided_by="kernel",
            evidence={"by": "ai rrr", **transition_evidence_extra},
        )

    # Retroactive recovery path: stitch the session into the audit
    # chain *and* archive its folder so it does not become a "ghost"
    # in sessions/ root. Guard against archiving a session the user
    # may still be working on (current_session) or a locked one.
    archived_to: Optional[Path] = None
    if retroactive and _is_archivable(session_path, project_root, config):
        archived_to = archive_session(session_path, config)
        loop.chain.append(
            "session.archived_retroactive",
            {
                "session_id": sid,
                "archive_path": str(archived_to.relative_to(project_root)),
                "decided_by": "kernel",
            },
        )
        console.print(
            f"[green]📦 retroactive archive:[/green] "
            f"{archived_to.relative_to(project_root)}"
        )

    console.print(
        Panel(
            f"[green]rrr complete[/green]\n"
            f"  graph_state: {loop.current()}\n"
            f"  RRR contract: PASS\n"
            f"  Acceptance evidence: "
            f"{'PASS' if (acc_report is None or acc_report.ok) else 'FAIL'}"
            + (
                f"\n  Archived to: {archived_to.relative_to(project_root)}"
                if archived_to else ""
            ),
            title="🏁 ai rrr",
            border_style="green",
        )
    )
    # Layer 5a — next-action footer
    console.print(
        render_one_line(
            compute_next(
                project_root,
                session_path=None if archived_to else session_path,
                graph_state=None if archived_to else loop.current(),
            )
        )
    )
    return 0


# ─────────── helpers ───────────


def _is_archivable(session_path: Path, project_root: Path, config) -> bool:
    """Retroactive auto-archive guards.

    Refuse to archive when:
      - the folder is already inside the configured archive dir
      - the session is the kernel's current_session (user may still
        be working on it)
      - a `.state/LOCK` file is present (something else holds it)
    """
    if not session_path.exists():
        return False
    paths_cfg = (config.raw_config or {}).get("paths", {})
    sessions_template = paths_cfg.get("sessions", "${ai_root}/sessions")
    archive_template = paths_cfg.get("archive_sessions", "${sessions}/archive")
    sessions_resolved = (
        sessions_template
        .replace("${ai_root}", str(config.ai_root))
        .replace("${project_root}", str(project_root))
    )
    archive_resolved = (
        archive_template
        .replace("${sessions}", sessions_resolved)
        .replace("${ai_root}", str(config.ai_root))
        .replace("${project_root}", str(project_root))
    )
    archive_dir = Path(archive_resolved).resolve()
    try:
        if archive_dir in session_path.resolve().parents:
            return False
    except OSError:
        return False

    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if cur and Path(cur).resolve() == session_path.resolve():
        return False

    if (session_path / ".state" / "LOCK").exists():
        return False
    return True


def _resolve_session(config) -> Path:
    state_mgr = StateManager(config)
    status = state_mgr.load_status()
    cur = status.get("current_session")
    if not cur:
        console.print(
            "[red]No active session. Cannot run rrr.[/red]"
        )
        raise typer.Exit(2)
    p = Path(cur)
    if not p.exists():
        console.print(f"[red]Session path missing: {p}[/red]")
        raise typer.Exit(2)
    return p


def _resolve_explicit_session(project_root: Path, ident: str) -> Path:
    """R14 — resolve a session by id, full path, or archive id.

    Back-compat alias for `core.session_resolver.resolve_explicit_session`
    (lifted from this file to a shared module in the KI-2026-05-16-001
    routing-drift fix). Preserves the original console.print + Exit(2)
    behaviour so rrr's 8 test callers see no change.
    """
    from ..core.session_resolver import (
        SessionNotFoundError,
        resolve_explicit_session,
    )
    try:
        return resolve_explicit_session(project_root, ident)
    except SessionNotFoundError as exc:
        console.print(
            f"[red]session not found: {ident}[/red]\n"
            f"  searched: {[str(c) for c in exc.candidates]}"
        )
        raise typer.Exit(2)


def _memory_retro_path(
    project_root: Path, retro_type: str, session_id: str
) -> Path:
    """Mint a sequential filename: <seq>_<date>_<HH>_<MM>_<ampm>_<type>-<slug>.md"""
    retros_dir = project_root / ".ai" / "memory" / "retros"
    retros_dir.mkdir(parents=True, exist_ok=True)
    seq = 1
    for f in retros_dir.iterdir():
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        try:
            n = int(f.name.split("_", 1)[0])
            seq = max(seq, n + 1)
        except (ValueError, IndexError):
            continue
    now = datetime.datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    hh = now.strftime("%I").lstrip("0") or "12"
    mm = now.strftime("%M")
    ampm = now.strftime("%p").lower()
    # session_id like "0001_2026-04-30_21_53_pm_feat-phase1-5-rrr-..."
    # slug = the trailing "<type>-<slug>" portion
    parts = session_id.split("_", 5)
    slug = parts[5] if len(parts) >= 6 else session_id
    if "-" in slug:
        existing_type, _, rest = slug.partition("-")
        # Honor explicit --type flag; if it differs, prepend it
        if existing_type != retro_type:
            slug = f"{retro_type}-{existing_type}-{rest}"
    else:
        slug = f"{retro_type}-{slug}"
    fname = f"{seq:04d}_{date_part}_{hh}_{mm}_{ampm}_{slug}.md"
    return retros_dir / fname


def _render_retro(
    metrics: SessionMetrics,
    acc_report: Optional[AcceptanceReport],
    fd_report: ForbiddenDiffReport,
    session_id: str,
) -> str:
    today = datetime.date.today().isoformat()
    acceptance_verdict = (
        "PASS" if (acc_report is None or acc_report.ok) else "FAIL"
    )
    rrr_contract = "PASS" if fd_report.ok and acceptance_verdict == "PASS" else "FAIL"

    lines: List[str] = [
        "---",
        f"session-id: {session_id}",
        "ritual: rrr",
        f"acceptance-evidence: {acceptance_verdict}",
        f"rrr-contract: {rrr_contract}",
        f"last-updated: {today}",
        "---",
        "",
        "# Retrospective",
        "",
        "## Verdict",
        "",
        f"- **Acceptance evidence:** {acceptance_verdict}",
        f"- **RRR contract:** {rrr_contract}",
        f"- **Forbidden-path violations:** {len(fd_report.violations)}",
        "",
        "## Metrics (computed from audit chain)",
        "",
        f"- session events: {metrics.event_count}",
        f"- graph transitions: {metrics.transition_count}",
        f"- iterations (gogogo steps): {metrics.iterations}",
        f"- gogogo verdicts: {metrics.gogogo_verdict_counts or '(none)'}",
        f"- NEEDS_HUMAN escalations: {metrics.needs_human_count}",
        f"- final graph_state: {metrics.final_graph_state}",
    ]
    if metrics.duration_seconds is not None:
        lines.append(
            f"- duration: {metrics.duration_seconds:.1f}s "
            f"({metrics.duration_seconds / 60:.1f} min)"
        )
    lines += ["", "## Graph transitions", ""]
    if metrics.transitions:
        for t in metrics.transitions:
            lines.append(
                f"- {t['from']} → {t['to']} via `{t['trigger']}` "
                f"({t['decided_by']})"
            )
    else:
        lines.append("(none recorded)")

    lines += ["", "## Acceptance evidence", ""]
    if acc_report is None:
        lines.append(
            "_no `THINK/03_ACCEPTANCE.yaml` provided — gate skipped_"
        )
    else:
        for r in acc_report.items:
            badge = "✅" if r.passed else "❌"
            lines.append(
                f"- {badge} **{r.item.id}** — {r.item.description or '(no description)'}"
            )
            lines.append(f"    - command: `{r.item.command}`")
            if r.passed:
                lines.append(f"    - exit: {r.exit_code}")
            else:
                lines.append(
                    "    - failures: " + "; ".join(r.failure_reasons)
                )

    lines += ["", "## Forbidden-path diff", ""]
    if fd_report.violations:
        lines.append("⚠️ violations detected:")
        for v in fd_report.violations:
            lines.append(f"- `{v}`")
    else:
        lines.append(
            f"✅ no D1 boundary writes (baseline: {fd_report.baseline})."
            + (
                " (.ai/audit/events.ndjson skipped — append-only by design)"
                if fd_report.skipped_audit_chain
                else ""
            )
        )

    lines += ["", "## Notes", ""]
    lines.append(
        "_Auto-generated by `ai rrr`. Add manual notes below this line._"
    )
    return "\n".join(lines) + "\n"


# ─────────── Phase 12 §3-4 retro_envelope.md production ───────────


RETRO_ENVELOPE_SCHEMA_VERSION = "trinity.retro_envelope.v1"


def _render_retro_envelope(
    *,
    session_path: Path,
    project_root: Path,
    sid: str,
    metrics: SessionMetrics,
    acc_report: Optional[AcceptanceReport],
    fd_report: ForbiddenDiffReport,
    baseline: str,
    tier: str,
    graph_state_final: str,
    chain: AuditChain,
) -> str:
    """Render the deterministic Phase 12 closure envelope.

    Output: YAML frontmatter (sort_keys=True for determinism) + a brief
    machine-rendered body. Schema per §4 of
    docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md. NO semantic content
    is permitted in this artifact (Article IX; spec §3.2).

    Idempotency: every field is sourced deterministically from session
    artifacts EXCEPT `ts_closed` which is wall-clock now (per spec §9
    C15: "byte-identical retro_envelope.md modulo ts_closed").
    """
    import hashlib
    import yaml as _yaml

    ts_closed = _utc_now_iso()
    ts_started = _load_session_started_at(session_path)
    duration_seconds = _compute_duration_seconds(ts_started, ts_closed)

    acceptance_results = _build_acceptance_results(acc_report)
    acceptance_summary = _build_acceptance_summary(acc_report)

    forbidden_violations = [
        {"path": str(v), "rule": "D1-forbidden-paths"}
        for v in fd_report.violations
    ]
    forbidden_diff_status = {
        "ok": fd_report.ok,
        "baseline": baseline,
        "violations": forbidden_violations,
    }

    baseline_untracked = _load_baseline_untracked_summary(session_path)
    audit_block = _build_audit_block(chain, sid)
    gogogo_verdicts = _normalize_gogogo_verdicts(metrics.gogogo_verdict_counts)
    artifact_paths = _enumerate_artifact_paths(session_path)
    indexed_retros = _enumerate_indexed_retros(project_root, sid)

    # memory_index_result is captured later in the rrr pipeline
    # (after _index_memory_cli runs). At envelope-render time it is
    # null; the corresponding rrr.completed audit row carries the
    # verbatim envelope per §6/§7. Documented as null here for that
    # ordering reason — not because the field is unsupported.
    memory_index_result = None

    frontmatter = {
        "schema_version": RETRO_ENVELOPE_SCHEMA_VERSION,
        "session_id": sid,
        "slug": _derive_slug(sid),
        "ts_started": ts_started,
        "ts_closed": ts_closed,
        "duration_seconds": duration_seconds,
        "tier": tier,
        "graph_state_final": graph_state_final,
        "decided_by": "kernel",
        "acceptance_results": acceptance_results,
        "acceptance_summary": acceptance_summary,
        "forbidden_diff_status": forbidden_diff_status,
        "baseline_untracked": baseline_untracked,
        "audit": audit_block,
        "transition_count": int(metrics.transition_count),
        "gogogo_verdicts": gogogo_verdicts,
        "iterations": int(metrics.iterations),
        "indexed_retros": indexed_retros,
        "artifact_paths": artifact_paths,
        "memory_index_result": memory_index_result,
    }

    # Canonical YAML serialization (sort_keys=True for determinism).
    # acceptance_results entries are dicts whose key-order is also
    # canonicalised by sort_keys=True; the LIST order is preserved
    # because PyYAML respects sequence order.
    yaml_text = _yaml.safe_dump(
        frontmatter,
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=False,
    )

    body_lines = [
        "---",
        yaml_text.rstrip("\n"),
        "---",
        "",
        "# retro_envelope (deterministic)",
        "",
        ("This is the mechanical closure envelope produced by `ai rrr` "
         "per Phase 12 §3-4."),
        ("All semantic reflection (lessons, root cause, doctrine) lives "
         "in companion `RETRO.md` — see Article IX."),
        "",
    ]
    return "\n".join(body_lines) + "\n"


def _utc_now_iso() -> str:
    """RFC3339 UTC timestamp with 'Z' suffix (matches AuditChain._now_iso)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _load_session_started_at(session_path: Path) -> Optional[str]:
    """Source: <session>/.state/session_state.json:created_at.

    Returns None if the file is missing or malformed (so the envelope
    holds an explicit null rather than guessing). Not a hard error —
    legacy sessions may pre-date the field.
    """
    state_path = session_path / ".state" / "session_state.json"
    if not state_path.is_file():
        return None
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    created = data.get("created_at")
    return created if isinstance(created, str) else None


def _compute_duration_seconds(
    ts_started: Optional[str], ts_closed: str
) -> Optional[int]:
    """Integer seconds between started and closed; None if either invalid."""
    if not ts_started:
        return None
    try:
        # Tolerate both '...Z' and '...+00:00' forms.
        s = ts_started.replace("Z", "+00:00")
        c = ts_closed.replace("Z", "+00:00")
        d_started = datetime.datetime.fromisoformat(s)
        d_closed = datetime.datetime.fromisoformat(c)
    except ValueError:
        return None
    return int((d_closed - d_started).total_seconds())


def _build_acceptance_results(
    acc_report: Optional[AcceptanceReport],
) -> List[dict]:
    """Per-criterion mechanical results (§4.2)."""
    if acc_report is None:
        return []
    out: List[dict] = []
    for r in acc_report.items:
        out.append({
            "id": r.item.id,
            "description": r.item.description or "",
            "command": r.item.command,
            "expect_exit": (
                int(r.item.expect_exit)
                if r.item.expect_exit is not None
                else None
            ),
            "actual_exit": (
                int(r.exit_code) if r.exit_code is not None else None
            ),
            "status": "PASS" if r.passed else "FAIL",
            "required": bool(r.item.required),
            "stdout_tail": (r.stdout or "")[-512:] if r.stdout else "",
            "stderr_tail": (r.stderr or "")[-512:] if r.stderr else "",
        })
    return out


def _build_acceptance_summary(
    acc_report: Optional[AcceptanceReport],
) -> dict:
    """Aggregate counts (§4.2 acceptance_summary)."""
    if acc_report is None:
        return {
            "total": 0,
            "pass": 0,
            "fail": 0,
            "skipped": 0,
            "required_failures": 0,
        }
    total = len(acc_report.items)
    passed = sum(1 for r in acc_report.items if r.passed)
    failed = sum(1 for r in acc_report.items if not r.passed)
    return {
        "total": total,
        "pass": passed,
        "fail": failed,
        "skipped": 0,
        "required_failures": len(acc_report.required_failures),
    }


def _load_baseline_untracked_summary(session_path: Path) -> Optional[dict]:
    """Return {sha256: <hash>, count: <int>} for the baseline_untracked
    snapshot at sss, or None when the file is missing.

    The file itself is a JSON list of paths; we sha256 its raw bytes so
    the envelope carries a stable anchor without re-listing every path.
    """
    p = session_path / ".state" / "baseline_untracked.json"
    if not p.is_file():
        return None
    try:
        import hashlib
        raw = p.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        try:
            data = json.loads(raw.decode("utf-8"))
            count = len(data) if isinstance(data, list) else 0
        except (json.JSONDecodeError, UnicodeDecodeError):
            count = 0
        return {"sha256": digest, "count": count}
    except OSError:
        return None


def _build_audit_block(chain: AuditChain, sid: str) -> dict:
    """Compute audit anchor (§4.3 audit.*).

    session_chain_head — last_hash() of the project audit chain (we
    don't yet have a per-session chain in this kernel build; the
    project chain is the canonical anchor — Spec 15 §3 alignment may
    introduce a per-session chain later, at which point this becomes
    the per-session head).

    last_seq — count of events for this session_id in the chain (a
    monotonically increasing integer; matches event ordering).
    """
    head = None
    last_seq = 0
    verify_status = "PASS"
    try:
        head = chain.last_hash()
        for ev in chain.iter_events():
            details = ev.get("details") if isinstance(ev, dict) else None
            if isinstance(details, dict) and details.get("session_id") == sid:
                last_seq += 1
    except Exception:  # noqa: BLE001 — defensive; envelope should not raise
        verify_status = "FAIL"
    return {
        "session_chain_head": head,
        "last_seq": int(last_seq),
        "verify_chain_status": verify_status,
    }


def _normalize_gogogo_verdicts(counts: Optional[Dict[str, int]]) -> dict:
    """Project SessionMetrics.gogogo_verdict_counts onto the §4.3 shape.

    Keys: PASS / FAIL / UNVERIFIED — counts default to 0.
    """
    src = dict(counts or {})
    return {
        "PASS": int(src.get("PASS", 0)),
        "FAIL": int(src.get("FAIL", 0)),
        "UNVERIFIED": int(src.get("UNVERIFIED", 0))
        + int(src.get("RETRY", 0))
        + int(src.get("NEEDS_HUMAN", 0)),
    }


def _enumerate_artifact_paths(session_path: Path) -> List[dict]:
    """Enumerate session-relative file paths + sha256 + size_bytes
    (§4.4 artifact_paths). Sorted by path for determinism. Skips
    .state/ (kernel-internal) to avoid noise in the manifest."""
    if not session_path.is_dir():
        return []
    out: List[dict] = []
    import hashlib
    for p in sorted(session_path.rglob("*")):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(session_path).as_posix()
        except ValueError:
            continue
        # Skip the .state/ kernel-internal tree to keep the manifest
        # focused on session-visible artifacts (THINK/, DO/, SANDBOX/).
        if rel.startswith(".state/"):
            continue
        # Skip retro_envelope.md itself to avoid self-referential hash
        # mutation (the file is being written; sha would be of partial
        # content). retro_envelope path is implicit at THINK/.
        if rel == "THINK/retro_envelope.md":
            continue
        try:
            raw = p.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            size = len(raw)
        except OSError:
            continue
        out.append({"path": rel, "sha256": sha, "size_bytes": size})
    return out


def _enumerate_indexed_retros(project_root: Path, sid: str) -> List[dict]:
    """List per-session retros under .ai/memory/retros/ that match the
    session's slug (§4.4 indexed_retros).

    Returns empty list when no retro file exists yet (e.g. dry-run, or
    pre-index ordering). Each entry is {path, sha256}.
    """
    retros_dir = project_root / ".ai" / "memory" / "retros"
    if not retros_dir.is_dir():
        return []
    slug = _derive_slug(sid)
    out: List[dict] = []
    import hashlib
    for f in sorted(retros_dir.iterdir()):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        # Loose match: slug substring (the retro filename embeds
        # <type>-<slug>; strict match would require parsing).
        if slug and slug not in f.name:
            continue
        try:
            raw = f.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
        except OSError:
            continue
        try:
            rel = f.relative_to(project_root).as_posix()
        except ValueError:
            rel = str(f)
        out.append({"path": rel, "sha256": sha})
    return out


def _derive_slug(sid: str) -> str:
    """Extract the trailing slug from a session id of shape
    NNNN_YYYY-MM-DD_HH_MM_AMPM_<type>-<slug>."""
    parts = sid.split("_", 5)
    return parts[5] if len(parts) >= 6 else sid


def _print_acceptance(report: AcceptanceReport) -> None:
    table = Table(title="Acceptance gate", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Required")
    table.add_column("Result")
    table.add_column("Description", style="dim")
    for r in report.items:
        result = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(
            r.item.id,
            "yes" if r.item.required else "no",
            result,
            r.item.description or "",
        )
    console.print(table)
    if report.required_failures:
        console.print(
            f"[red]{len(report.required_failures)} required acceptance "
            f"item(s) failed[/red]"
        )


def _print_forbidden_diff(report: ForbiddenDiffReport) -> None:
    if report.ok:
        console.print(
            f"[green]forbidden-path diff: ✅ none (baseline: "
            f"{report.baseline})[/green]"
        )
    else:
        console.print(
            f"[red]forbidden-path diff: ❌ "
            f"{len(report.violations)} violation(s)[/red]"
        )
        for v in report.violations:
            console.print(f"  - {v}")
    if report.carve_outs:
        console.print(
            f"[yellow]forbidden-path carve-outs (allowed by "
            f"plan_envelope.allowed_paths): "
            f"{len(report.carve_outs)} path(s)[/yellow]"
        )
        for c in report.carve_outs:
            console.print(f"  - {c}")


def _load_plan_envelope_allowed_paths(
    session_path: Path,
) -> Optional[List[str]]:
    """Return the active session's plan_envelope.allowed_paths list, or
    None when no readable source is found.

    Source priority:
      1. `.state/plan.json` — kernel-canonical, always written by `ai nnn`
         (carries approved_by/approved_at/budget_status added by the kernel).
      2. `THINK/plan_envelope.json` — operator-mirrored copy (legacy
         Phase 0.5 location; still honoured for back-compat).

    Closed-fail: any error returns None so the verifier behaves as it did
    before Phase 0.5 — the safe default.
    """
    for candidate in (
        session_path / ".state" / "plan.json",
        session_path / "THINK" / "plan_envelope.json",
    ):
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        paths = data.get("allowed_paths") if isinstance(data, dict) else None
        if not isinstance(paths, list):
            continue
        return [p for p in paths if isinstance(p, str)]
    return None


def _index_memory_cli(
    project_root: Path, memory_retro_path: Path
) -> ToolInvocation:
    """Delegate retro indexing to `memory-cli index <retro-path>`.

    Article IX (Memory Discipline): memory retrieves evidence — it never
    derives semantic truth. The previous Phase 2.2 path used the
    deprecated `learn` verb which performed semantic derivation
    (auto-tag, embed, confidence inference); under Trinity Constitution
    v1.0 that path is constitutional role-collapse.

    Best-effort: returns the ToolInvocation regardless of success so
    the caller can summarize it for the audit chain. Severity-by-tier
    (Addendum §B) is applied at the caller, not here.
    """
    return call_tool(
        project_root,
        "memory-cli",
        f"index {memory_retro_path}",
        timeout_seconds=15,
    )


def _memory_index_ok(inv: ToolInvocation) -> bool:
    """True iff memory-cli index reported success, including R47
    signal-exit recovery (envelope.ok=true + native abort)."""
    if inv.ok and inv.envelope and inv.envelope.get("ok") is True:
        return True
    if (
        inv.envelope is not None
        and inv.envelope.get("ok") is True
        and inv.returncode is not None
        and inv.returncode < 0
    ):
        return True
    return False


def _summarize_memory_index(inv: ToolInvocation) -> dict:
    """Audit-chain payload for memory-cli index — the v0.1 `memory.index`
    action result (artifact-level: indexed_new / indexed_updated /
    artifacts_total / chunks_total / schema)."""
    if inv.ok and inv.envelope:
        data = inv.envelope.get("data") or {}
        return {
            "ok": True,
            "indexed_new": data.get("indexed_new"),
            "indexed_updated": data.get("indexed_updated"),
            "artifacts_total": data.get("artifacts_total"),
            "chunks_total": data.get("chunks_total"),
            "schema": data.get("schema"),
            "tool_version": inv.envelope.get("tool_version"),
        }
    # R47: false-negative recovery — memory-cli emits envelope to stdout
    # BEFORE the SIGABRT in libc++ destructor (fastembed/sqlite-vec
    # native module destructor race on macOS). If envelope.ok=true and
    # the process exited via signal (returncode<0), the SQLite WAL has
    # already committed; trust the envelope. (memory-cli v0.1 core does
    # not load the offending native modules, so this branch only fires
    # under MEMORY_CLI_LEGACY=1 — but we keep it as defence-in-depth.)
    if (
        inv.envelope is not None
        and inv.envelope.get("ok") is True
        and inv.returncode is not None
        and inv.returncode < 0
    ):
        data = inv.envelope.get("data") or {}
        return {
            "ok": True,
            "indexed_new": data.get("indexed_new"),
            "indexed_updated": data.get("indexed_updated"),
            "artifacts_total": data.get("artifacts_total"),
            "chunks_total": data.get("chunks_total"),
            "schema": data.get("schema"),
            "tool_version": inv.envelope.get("tool_version"),
            "note": (
                f"signal_exit returncode={inv.returncode}; "
                f"envelope.ok=true; data confirmed via stdout"
            ),
        }
    return {
        "ok": False,
        "error": inv.error
        or (
            inv.envelope.get("error", {}).get("message")
            if inv.envelope and inv.envelope.get("error")
            else None
        )
        or f"returncode={inv.returncode}",
    }


def _print_memory_index(inv: ToolInvocation, tier: str = "WARM") -> None:
    if inv.ok and inv.envelope:
        data = inv.envelope.get("data") or {}
        console.print(
            f"[green]memory-cli index:[/green] "
            f"indexed_new={data.get('indexed_new')} "
            f"indexed_updated={data.get('indexed_updated')} "
            f"chunks_total={data.get('chunks_total')}"
        )
        return
    if (
        inv.envelope is not None
        and inv.envelope.get("ok") is True
        and inv.returncode is not None
        and inv.returncode < 0
    ):
        data = inv.envelope.get("data") or {}
        console.print(
            f"[yellow]memory-cli index:[/yellow] recovered (signal exit "
            f"returncode={inv.returncode}, data persisted) "
            f"indexed_new={data.get('indexed_new')}"
        )
        return
    # T3 severity by tier (Addendum §B): visible failure is mandatory
    # under Article XXIII, but the gate consequence varies by tier.
    detail = inv.error or (
        inv.envelope.get("error", {}).get("message")
        if inv.envelope and inv.envelope.get("error")
        else f"returncode={inv.returncode}"
    )
    severity = _index_severity_for_tier(tier, ok=False)
    style = {"warning": "yellow", "degraded": "yellow", "block": "red"}.get(
        severity, "yellow"
    )
    console.print(
        f"[{style}]memory-cli index {severity.upper()}:[/{style}] {detail} "
        f"(tier={tier}; retro file is the source of truth)"
    )


# T3 severity-by-tier (Addendum §B): the rrr gate's response to a
# memory-index failure depends on the session's Decision Velocity Tier.
def _index_severity_for_tier(tier: Optional[str], ok: bool) -> str:
    """Return one of: 'pass', 'warning', 'degraded', 'block'.

    HOT  fail → warning (rrr completes, surface in stdout)
    WARM fail → degraded (rrr completes with FAILED_VISIBLE in audit)
    COLD fail → block (caller MUST treat as required-failure)
    """
    if ok:
        return "pass"
    t = (tier or "WARM").upper()
    if t == "HOT":
        return "warning"
    if t == "COLD":
        return "block"
    return "degraded"


def _memory_index_blocks_completion(
    index_severity: str,
    *,
    retroactive: bool = False,
) -> bool:
    """True when memory index severity must refuse RETRO->DONE."""
    return index_severity == "block" and not retroactive


def _load_plan_envelope_tier(session_path: Path) -> str:
    """Read the session's declared Decision Velocity Tier from
    plan_envelope.json. Default WARM (Addendum §B mid-tier) when absent
    or malformed — closed-conservative."""
    envelope_path = session_path / "THINK" / "plan_envelope.json"
    if not envelope_path.exists():
        return "WARM"
    try:
        data = json.loads(envelope_path.read_text())
    except (OSError, json.JSONDecodeError):
        return "WARM"
    if not isinstance(data, dict):
        return "WARM"
    raw = data.get("tier")
    if not isinstance(raw, str):
        return "WARM"
    t = raw.strip().upper()
    if t not in ("HOT", "WARM", "COLD"):
        return "WARM"
    return t


def _sha256_of_file(path: Path) -> str:
    """sha256 hex of a file's raw bytes. Used for T4 delegation audit
    so the audit chain hash-pins the artifact rrr handed to memory-cli.
    Returns empty string on read error (best-effort — audit shape stays
    consistent)."""
    try:
        import hashlib
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def _maybe_suggest_pin(
    chain: AuditChain,
    sid: str,
    memory_retro_path: Path,
    project_root: Path,
) -> None:
    """Print a pin-suggestion ONLY when the session contains a human
    decision (decided_by='human' in some prior event). Suggestion is
    stdout-only; rrr never auto-pins (Article V — Kernel governs, does
    not execute; T1 — rrr may not synthesize institutional memory;
    closing principle 2 — Memory pinning confers authority)."""
    human_decision = False
    for ev in chain.iter_events():
        details = ev.get("details") if isinstance(ev, dict) else None
        if not isinstance(details, dict):
            continue
        if details.get("session_id") != sid:
            continue
        if details.get("decided_by") == "human":
            human_decision = True
            break
    if not human_decision:
        return
    rel = memory_retro_path.relative_to(project_root)
    # Slug from the retro filename for the suggested alias name.
    slug = memory_retro_path.stem.replace(".", "-")[:60]
    console.print(
        f"[cyan]suggest:[/cyan] this session contains a human decision. "
        f"To mark the retro canonical, run "
        f"[bold]memory-cli pin {rel} --as=retro-{slug} "
        f"--reason='<your reason>'[/bold]. "
        f"(rrr will never auto-pin; pinning is authority decision.)"
    )


def _print_metrics(m: SessionMetrics) -> None:
    table = Table(title="Session metrics", show_header=False)
    table.add_column("k", style="cyan")
    table.add_column("v")
    table.add_row("session_id", m.session_id)
    table.add_row("event_count", str(m.event_count))
    table.add_row("transition_count", str(m.transition_count))
    table.add_row("iterations", str(m.iterations))
    table.add_row(
        "gogogo_verdicts",
        json.dumps(m.gogogo_verdict_counts) if m.gogogo_verdict_counts else "(none)",
    )
    table.add_row("needs_human_count", str(m.needs_human_count))
    table.add_row("final_graph_state", str(m.final_graph_state))
    if m.duration_seconds is not None:
        table.add_row("duration_min", f"{m.duration_seconds / 60:.1f}")
    console.print(table)

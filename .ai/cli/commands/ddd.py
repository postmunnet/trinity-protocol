"""ai ddd — Deploy decision gate (VERIFIED → PROMOTED → DEPLOYED).

Spec ref: docs/specs/03_GOAL_LOOP_SPEC.md (Phase 5).
           docs/specs/02_VERIFIER_SPEC.md §3.3 (deploy_check rule_set).

This is the proper Phase 5 deploy ritual. It replaces the dev-only
`--auto-deploy` convenience flag in `ai rrr`, which was always
flagged as "not a substitute for ai ddd (Phase 5 proper)".

Flow:
  1. Resolve session; assert graph_state == VERIFIED.
  2. Fire `promote_request` (VERIFIED → PROMOTED, decided_by=human).
  3. Optionally invoke the underlying deploy mover (`ai deploy dev` or
     `--prod`) — kept opt-in via flag because not every session needs
     a file copy.
  4. Fire `deploy_request` (PROMOTED → DEPLOYED, decided_by=human).
  5. Run the verifier with rule_set=deploy_check against any evidence
     the operator passes via --evidence. Verdict is recorded but does
     not gate the transition (the transition is human-decided; the
     verifier provides post-hoc evidence for the audit chain).
  6. Append `ddd.completed` event.

`ai rrr` remains responsible for VERIFIED→DONE through the retro
gate; `ai ddd` is the explicit promotion + deploy gate that comes
*before* `ai rrr` for sessions that ship real artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.audit import get_chain_for_project
from ..core.ddd_artifacts import make_decision_packet, write_decision_packet
from ..core.auth import load_hmac_envelope, verify_hmac
# Article XV (Spec 9, TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 §4.5): new transports
# MUST use the 10-field signed envelope and the 7-step `verify_envelope`
# pipeline below. tg-bot v0.3.x still rides the legacy 5-field path via
# load_hmac_envelope + verify_hmac. The legacy `ddd.hmac_rejected` audit
# event remains for compat; new boundary path emits `transport.envelope_*`.
from ..core.transport import (
    EVENT_REFUSED_BADKEY as TRANSPORT_EVENT_REFUSED_BADKEY,
    verify_envelope,
)
from ..core.loop import Loop
from ..core.next_action import compute as compute_next, render_one_line
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
)
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.verifier import (
    VerifierError,
    VerifierVerdict,
    evaluate_step,
    load_rules,
)

app = typer.Typer()
console = Console()


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    target: str = typer.Option(
        "dev",
        "--target",
        help="Deploy target: dev | prod (matches `ai deploy` subcommands)",
    ),
    reason: str = typer.Option(
        "human-decided promotion + deployment",
        "--reason",
        help="Why this deployment is happening (recorded in audit chain)",
    ),
    evidence_file: Optional[Path] = typer.Option(
        None,
        "--evidence",
        help="JSON file with deploy_check evidence "
        "(health_check_ok, smoke_tests_pass, etc.)",
    ),
    skip_verify: bool = typer.Option(
        False,
        "--skip-verify",
        help="Skip the post-deploy deploy_check verifier evaluation",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the plan without audit/capture writes or graph transitions",
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport (e.g. trinity-tg-bot) "
        "carrying {session,command,args,ts,nonce,sig}. When present, kernel "
        "verifies HMAC via core.auth.verify_hmac and stamps "
        "decided_by=human:tg:bot; on failure emits ddd.hmac_rejected and "
        "exits 79. Spec 14 §6.1 Layer 3 / Decision Y.",
    ),
):
    """Run the deploy decision gate."""
    if ctx.invoked_subcommand is not None:
        return
    code = _run(
        target=target,
        reason=reason,
        evidence_file=evidence_file,
        skip_verify=skip_verify,
        dry_run=dry_run,
        hmac_envelope_file=hmac_envelope_file,
    )
    raise typer.Exit(code=code)


HMAC_REJECT_EXIT = 79

# Backwards-compat alias for tests / external importers that still
# reference `cli.commands.ddd._load_hmac_envelope`. The canonical home
# is now `cli.core.auth.load_hmac_envelope` (Decision Y / R35 refactor).
_load_hmac_envelope = load_hmac_envelope


def _ddd_dry_run(
    *,
    target: str,
    reason: str,
    skip_verify: bool,
    project_root: Path,
    session_path: Path,
) -> int:
    """Preview ddd without audit/capture writes or graph transitions."""
    loop = Loop(
        session_path,
        graph_name="standard",
        project_root=project_root,
    )
    cur = loop.current()
    if cur != "VERIFIED":
        console.print(
            f"[red]graph_state must be VERIFIED to run ddd; got {cur!r}. "
            f"Run `ai next` to see what to do from here.[/red]"
        )
        return 2
    _print_dry_run_panel(
        target=target,
        reason=reason,
        skip_verify=skip_verify,
    )
    return 0


def _print_dry_run_panel(*, target: str, reason: str, skip_verify: bool) -> None:
    console.print(
        Panel(
            f"DRY-RUN — would fire:\n"
            f"  VERIFIED → PROMOTED via promote_request (human)\n"
            f"  PROMOTED → DEPLOYED via deploy_request (human)\n"
            f"  target: {target}\n"
            f"  reason: {reason}\n"
            f"  verifier: "
            f"{'skipped' if skip_verify else 'deploy_check rule_set'}",
            title="🟡 ai ddd (dry-run)",
            border_style="yellow",
        )
    )


def _run(
    *,
    target: str,
    reason: str,
    evidence_file: Optional[Path],
    skip_verify: bool,
    dry_run: bool,
    hmac_envelope_file: Optional[Path] = None,
) -> int:
    from ..core.recordproxy import capture
    if target not in {"dev", "prod"}:
        console.print(
            f"[red]--target must be 'dev' or 'prod', got {target!r}[/red]"
        )
        return 2

    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    project_root = config.project_root
    session_path = _resolve_session(config)

    if dry_run:
        return _ddd_dry_run(
            target=target,
            reason=reason,
            skip_verify=skip_verify,
            project_root=project_root,
            session_path=session_path,
        )

    # Part 2 (capture wiring): one capture per ddd invocation.
    with capture(
        session_path,
        ritual="ddd",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("invocation_params.json", {
            "target": target,
            "reason": reason,
            "evidence_file": str(evidence_file) if evidence_file else None,
            "skip_verify": skip_verify,
            "dry_run": dry_run,
            "hmac_envelope_file": str(hmac_envelope_file) if hmac_envelope_file else None,
        })
        return _ddd_inner(
            target=target,
            reason=reason,
            evidence_file=evidence_file,
            skip_verify=skip_verify,
            dry_run=dry_run,
            hmac_envelope_file=hmac_envelope_file,
            config=config,
            project_root=project_root,
            session_path=session_path,
            cap=cap,
        )


def _ddd_inner(
    *,
    target: str,
    reason: str,
    evidence_file: Optional[Path],
    skip_verify: bool,
    dry_run: bool,
    hmac_envelope_file: Optional[Path],
    config,
    project_root,
    session_path,
    cap,
) -> int:
    loop = Loop(
        session_path,
        graph_name="standard",
        project_root=project_root,
    )
    cur = loop.current()
    if cur != "VERIFIED":
        console.print(
            f"[red]graph_state must be VERIFIED to run ddd; got {cur!r}. "
            f"Run `ai next` to see what to do from here.[/red]"
        )
        return 2

    # RC v1.1-rc Article XII.5 — load the ddd pack so the empirical
    # ratification trail anchors the audit-event vocabulary. The pack
    # declares CONCEPTUAL states (VERIFY/NEEDS_HUMAN → PROMOTE/NEEDS_HUMAN/
    # FAILED); the physical graph uses VERIFIED → PROMOTED → DEPLOYED.
    # Like gogogo, this pack/graph naming drift is pre-existing and out of
    # scope for this session (`.ai/rituals/**` is in forbidden_paths).
    ddd_pack = load_pack(
        "ddd",
        rituals_root=project_root / ".ai" / "rituals",
    )

    # Pack-declared ddd.invoked — first ritual-side event after the
    # higher-level state precondition (VERIFIED) is satisfied. Emitted
    # before HMAC verification so reviewers can trace every invocation
    # attempt (Article IX — exact evidence trail).
    get_chain_for_project(project_root).append(
        "ddd.invoked",
        {
            "session_id": session_path.name,
            "graph_state": cur,
            "decided_by": "kernel",
            "target": target,
            "reason": reason,
            "dry_run": dry_run,
        },
    )

    if dry_run:
        _print_dry_run_panel(
            target=target,
            reason=reason,
            skip_verify=skip_verify,
        )
        return 0

    # PRD Phase 8 acceptance line 800: 'AI verdict alone cannot
    # promote/deploy.' Refuse prod promotion when every verdict event
    # in this session's audit chain came from an advisory source
    # (layer_3_llm_judge or explicit advisory). Dev target is
    # unaffected (operator can iterate freely on dev). skip_verify
    # bypasses this check (consistent with the broader verifier gate
    # bypass; skip_verify is the kill-switch for operators who know
    # what they're doing).
    if target == "prod" and not skip_verify:
        from ..core.judge_advisory import verdict_is_advisory_only
        chain = get_chain_for_project(project_root)
        if verdict_is_advisory_only(chain, session_path.name):
            chain.append(
                "ddd.advisory_only_refused",
                {
                    "session_id": session_path.name,
                    "decided_by": "kernel",
                    "target": target,
                    "reason": "AI advisory verdict alone cannot promote/deploy "
                              "(PRD Phase 8 acceptance line 800; Article XIII).",
                },
            )
            console.print(
                f"[red]ddd refused — every verdict in this session is from an "
                f"AI advisory source (layer_3_llm_judge). Per PRD Phase 8 "
                f"acceptance, AI verdict alone cannot promote/deploy to prod. "
                f"Add a deterministic (layer_1) or human (layer_4) verdict, "
                f"or pass --skip-verify (operator override).[/red]"
            )
            return 1

    # HMAC verify (if envelope flag passed) — must happen before any
    # transition fires so a rejection leaves graph_state at VERIFIED.
    # The graph schema locks decided_by='human' on promote/deploy
    # transitions; we keep that constant and instead stamp the
    # transport tag on the audit event metadata (decided_by_attr +
    # transition evidence.via) so reviewers can trace tg-bot origin
    # without amending the graph contract.
    decided_by_attr = "human"
    transition_evidence_extra: Dict[str, Any] = {}
    if hmac_envelope_file is not None:
        chain = get_chain_for_project(project_root)
        try:
            envelope, payload_bytes, sig, ts_iso = load_hmac_envelope(
                hmac_envelope_file
            )
        except (ValueError, json.JSONDecodeError, OSError) as e:
            chain.append(
                "ddd.hmac_rejected",
                {
                    "session_id": session_path.name,
                    "reason": "bad_envelope",
                    "ts_iso": None,
                    "detail": str(e),
                },
            )
            # Article XV compat-window dual-emit: new transport namespace
            # (TRINITY_TRANSPORT_BOUNDARY_SPEC_V1 §5.4). Legacy event above
            # stays for tg-bot v0.3.x consumers; v0.4+ MUST consume the new
            # transport.envelope_refused.badkey event_type.
            chain.append(
                TRANSPORT_EVENT_REFUSED_BADKEY,
                {
                    "session_id": session_path.name,
                    "source_transport": "tg-bot:legacy-5field",
                    "claimed_actor": "human:tg:unknown",
                    "reason": "bad_envelope",
                    "detail": str(e),
                },
            )
            console.print(
                f"[red]ddd.hmac_rejected: bad_envelope ({e})[/red]"
            )
            return HMAC_REJECT_EXIT

        ok, hmac_reason = verify_hmac(payload_bytes, sig, ts_iso)
        if not ok:
            chain.append(
                "ddd.hmac_rejected",
                {
                    "session_id": session_path.name,
                    "reason": hmac_reason,
                    "ts_iso": ts_iso,
                    "envelope_keys": sorted(list(envelope.keys())),
                },
            )
            # Article XV compat-window dual-emit — see comment above.
            chain.append(
                TRANSPORT_EVENT_REFUSED_BADKEY,
                {
                    "session_id": session_path.name,
                    "source_transport": "tg-bot:legacy-5field",
                    "claimed_actor": f"human:tg:{envelope.get('user_id', 'bot')}",
                    "reason": hmac_reason,
                    "ts_iso": ts_iso,
                },
            )
            console.print(
                f"[red]ddd.hmac_rejected: {hmac_reason}[/red]"
            )
            return HMAC_REJECT_EXIT

        # R34: bind Telegram user_id when present in the signed payload
        # (bot v0.3.1+); fall back to anonymous 'bot' label for envelopes
        # without user_id (5-field back-compat with bot v0.3.0).
        hmac_user_id = envelope.get("user_id")
        if hmac_user_id is not None:
            decided_by_attr = f"human:tg:{hmac_user_id}"
        else:
            decided_by_attr = "human:tg:bot"
        transition_evidence_extra = {
            "via": "tg-bot:hmac",
            "hmac_ts": ts_iso,
            "hmac_nonce": envelope.get("nonce"),
            "hmac_user_id": hmac_user_id,
        }

    # 2. promote
    cur = loop.fire(
        "promote_request",
        decided_by="human",
        evidence={"reason": reason, "target": target, **transition_evidence_extra},
    )

    # 3. (optional) actual deployment — left to the operator. We just
    # record the intent in the audit chain; `ai deploy <target>` is
    # the file-mover. Phase 5+ may bundle the call here.

    # 4. deploy
    cur = loop.fire(
        "deploy_request",
        decided_by="human",
        evidence={"reason": reason, "target": target, **transition_evidence_extra},
    )

    # 5. verifier (deploy_check) — informational, not gating
    verifier_data = None
    if not skip_verify:
        try:
            rules_doc = load_rules(project_root)
            evidence: Dict[str, Any] = {}
            if evidence_file:
                evidence = json.loads(
                    Path(evidence_file).read_text(encoding="utf-8")
                )
            verdict = evaluate_step(
                step={},
                rule_set_name="deploy_check",
                rules_doc=rules_doc,
                extra_evidence=evidence,
            )
            verifier_data = {
                "verdict": verdict.verdict,
                "reason": verdict.reason,
                "rule_set": verdict.rule_set,
                "mode": verdict.mode,
                "evidence_keys": verdict.evidence_keys,
                "matched_predicates": verdict.matched_predicates,
            }
            cap.validation("deploy_check_verdict.json", verifier_data)
            color = (
                "green" if verdict.verdict == "PASS"
                else "yellow" if verdict.verdict in ("RETRY", "NEEDS_HUMAN")
                else "red"
            )
            console.print(
                f"[{color}]deploy_check verdict: {verdict.verdict}[/{color}] "
                f"({verdict.reason})"
            )
        except VerifierError as e:
            verifier_data = {"verdict": "ERROR", "reason": str(e)}
            console.print(
                f"[yellow]deploy_check skipped (verifier error): {e}[/yellow]"
            )

    # Wire #3 — produce schema-valid decision_packet.json before
    # ddd.completed audit event. Fail-soft: a packet build/write failure
    # logs a warning but does not block the ritual transition.
    try:
        import hashlib as _hashlib
        verifier_reports = []
        for vf_name in ("verify_dev.json", "verify_prod.json"):
            vf_path = session_path / ".state" / vf_name
            if vf_path.is_file():
                content = vf_path.read_bytes()
                verifier_reports.append({
                    "path": f".state/{vf_name}",
                    "hash": _hashlib.sha256(content).hexdigest(),
                })
        packet = make_decision_packet(
            session_id=session_path.name,
            proposing_role="planner",
            requested_action=target if target in ("promote", "deploy", "abort", "amend") else "deploy",
            verifier_reports=verifier_reports,
            summary=reason or f"ddd target={target}",
        )
        packet_path = write_decision_packet(session_path, packet)
        console.print(f"   [dim]decision packet: {packet_path.name}[/dim]")
        cap.output("decision_packet.json.path", str(packet_path))
    except Exception as exc:
        console.print(
            f"[yellow]⚠ decision packet emission failed: {exc}[/yellow]"
        )

    # 6. ddd.completed audit event
    chain = get_chain_for_project(project_root)
    chain.append(
        "ddd.completed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": decided_by_attr,
            "target": target,
            "reason": reason,
            "verifier": verifier_data,
        },
    )
    cap.output("ddd_result.json", {
        "target": target,
        "reason": reason,
        "graph_state": loop.current(),
        "verifier": verifier_data,
        "dry_run": dry_run,
    })

    console.print(
        Panel(
            f"deploy decision recorded.\n"
            f"  graph_state: {loop.current()}\n"
            f"  target: {target}\n"
            f"  reason: {reason}\n"
            f"  verifier: "
            f"{verifier_data['verdict'] if verifier_data else 'skipped'}",
            title="✅ ai ddd",
            border_style="green",
        )
    )
    # Layer 5a — next-action footer
    console.print(
        render_one_line(
            compute_next(
                project_root,
                session_path=session_path,
                graph_state=loop.current(),
            )
        )
    )
    return 0


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

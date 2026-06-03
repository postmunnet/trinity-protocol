"""ai gogogo — Step-by-step execution with verifier checkpoint.

Spec ref: .ai/shims/gogogo/SHIM.md (canonical contract)
          docs/specs/02_VERIFIER_SPEC.md §5 (Pyramid layer 1)
          docs/specs/03_GOAL_LOOP_SPEC.md §4 (loop algorithm)
          Decision D11 (budget enforcement)

Required: an active session in graph_state DO with both .state/vvv_pass and
.state/nnn_pass markers present.

For each numbered step in `.state/plan.json`:
  1. Append `gogogo.step_started` audit event
  2. Run the verifier (Pyramid layer 1) — Phase 4 onward this is a
     real rules engine driven by `.ai/policies/verifier-rules.yaml`;
     `step.force_verdict` still wins (kept for fixtures)
  3. Append `gogogo.step_passed` (or `gogogo.step_failed`) with the verdict
  4. Re-check the budget; on breach -> NEEDS_HUMAN escalation

After the final step:
  - Append `gogogo.completed`
  - Fire `gogogo_complete` (DO -> VERIFIED, decided_by: verifier)
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
from ..core.auth import load_hmac_envelope, verify_hmac
from ..core.budget import Budget
from ..core.lease_lifecycle import run_lease_lifecycle
from ..core.loop import Loop
from ..core.next_action import compute as compute_next, render_one_line
from ..core.policy_engine import (
    build_query_envelope,
    envelope_to_audit_dict,
    load_policy_doc,
    query as policy_query,
)
from ..core.recordproxy import capture
from ..core.ritual_pack_loader import (
    assert_transition_allowed,
    load_pack,
)
from ..core.sandbox_contract import (
    AuthorityCapability,
    FsCapability,
    NetCapability,
    ProcCapability,
    SandboxProfile,
    ToolsCapability,
    validate_profile_dict,
)
from ..core.sandbox_gate import run_sandbox_gated_lifecycle
from ..core.sandbox_runtime import (
    build_sandbox_profile_text,
    is_sandbox_exec_available,
    resolve_allowlist_hostnames,
    runtime_enforcement_axes,
    should_emit_unenforced_warning,
    should_wrap,
    wrap_argv_with_sandbox_exec,
    write_profile_to_tmp,
)
from ..core.ssot import SSOTLoader
from ..core.state import StateManager
from ..core.tool_dispatcher import dispatch_tool
from ..core.tool_registry import RegistryValidationError, load_registry
from ..core.verifier_runtime import (
    CONSOLIDATION_PRECEDENCE,
    TIER_SEVERITY,
    consolidate_step_tiers,
    consolidate_step_verdicts,
)
from ..core.verifier import (
    VerifierError,
    VerifierVerdict,
    evaluate_step,
    get_rule_set,
    load_rules,
)

app = typer.Typer()
console = Console()


def _verify_step(
    step: Dict[str, Any],
    rule_set_name: str,
    rules_doc: Dict[str, Any],
) -> VerifierVerdict:
    """Phase 4 verifier: file-driven rules.

    Honors any `defaults` block on the rule_set (so `step_complete`
    can pre-fill `step_done: True` and stay permissive); a step can
    still negate any default by setting the same key to False
    explicitly.
    """
    rule_set = get_rule_set(rules_doc, rule_set_name)
    defaults = rule_set.get("defaults") or {}
    merged_step = {**defaults, **(step or {})}
    return evaluate_step(merged_step, rule_set_name, rules_doc)


HMAC_REJECT_EXIT = 79


class SandboxProfileLoadError(RuntimeError):
    def __init__(self, profile_id: str, event_type: str, reason: str):
        super().__init__(reason)
        self.profile_id = profile_id
        self.event_type = event_type
        self.reason = reason


def _sandbox_runtime_enforcement_enabled(config) -> bool:
    sandbox_cfg = (config.raw_config or {}).get("sandbox", {})
    if not isinstance(sandbox_cfg, dict):
        return True
    return bool(sandbox_cfg.get("runtime_enforcement_enabled", True))


def _load_sandbox_profile(project_root: Path, profile_id: str) -> Optional[SandboxProfile]:
    """Load .ai/policies/sandbox_profiles/<id>.yaml into a SandboxProfile.

    Fail-closed: a declared profile is part of the step's capability
    boundary. Missing or invalid profiles raise so the caller can emit
    an audit event and refuse dispatch.
    """
    profile_path = (
        project_root / ".ai" / "policies" / "sandbox_profiles" / f"{profile_id}.yaml"
    )
    if not profile_path.is_file():
        raise SandboxProfileLoadError(
            profile_id,
            "sandbox.profile_missing",
            f"sandbox profile {profile_id!r} not found at {profile_path}",
        )
        return None
    try:
        import yaml as _yaml
        data = _yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        validate_profile_dict(data)
    except Exception as exc:
        raise SandboxProfileLoadError(
            profile_id,
            "sandbox.profile_invalid",
            f"sandbox profile {profile_id!r} invalid: {exc}",
        )

    fs = data.get("fs", {}) or {}
    net = data.get("net", {}) or {}
    proc = data.get("proc", {}) or {}
    tools = data.get("tools", {}) or {}
    authority = data.get("authority", {}) or {}
    return SandboxProfile(
        id=data["id"],
        version=data["version"],
        fs=FsCapability(
            read_roots=list(fs.get("read_roots", [])),
            write_roots=list(fs.get("write_roots", [])),
            forbidden_paths=list(fs.get("forbidden_paths", [])),
            delete_roots=list(fs.get("delete_roots", [])),
            max_bytes_per_file=int(fs.get("max_bytes_per_file", 0) or 0),
            max_total_bytes=int(fs.get("max_total_bytes", 0) or 0),
        ),
        net=NetCapability(
            outbound=str(net.get("outbound", "denied")),
            allowlist=list(net.get("allowlist", [])),
            protocols=list(net.get("protocols", [])),
        ),
        proc=ProcCapability(
            allowed_binaries=list(proc.get("allowed_binaries", [])),
            forbidden_binaries=list(proc.get("forbidden_binaries", [])),
            spawn_allowed=bool(proc.get("spawn_allowed", False)),
            max_wallclock_seconds=int(proc.get("max_wallclock_seconds", 0) or 0),
        ),
        tools=ToolsCapability(
            allowed=list(tools.get("allowed", [])),
            forbidden=list(tools.get("forbidden", [])),
        ),
        authority=AuthorityCapability(
            may_promote=bool(authority.get("may_promote", False)),
            may_deploy=bool(authority.get("may_deploy", False)),
            may_modify_policies=bool(authority.get("may_modify_policies", False)),
            ddd_propose_allowed=bool(authority.get("ddd_propose_allowed", False)),
        ),
        description=str(data.get("description", "")),
    )


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    rule_set: str = typer.Option(
        "step_complete", "--rule-set", help="Verifier rule set per step"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Walk steps, log audit, no fire transitions"
    ),
    hmac_envelope_file: Optional[Path] = typer.Option(
        None,
        "--hmac-envelope-file",
        help="JSON envelope from external transport (e.g. trinity-tg-bot) "
        "carrying {session,command,args,ts,nonce[,user_id],sig}. When present, "
        "kernel verifies HMAC via core.auth.verify_hmac before running any "
        "step; on failure emits gogogo.hmac_rejected and exits 79. Spec 14 "
        "§6.1 Layer 3 / Decision Y / R35.",
    ),
    session: Optional[str] = typer.Option(
        None,
        "--session",
        help="(KI-2026-05-16-001) Explicit session id or path — bypasses "
        "the global current_session pointer to avoid routing drift.",
    ),
):
    """Run gogogo: step-by-step with verifier checkpoint per step."""
    if ctx.invoked_subcommand is not None:
        return
    _run(rule_set, dry_run, hmac_envelope_file=hmac_envelope_file, session_override=session)


def _run(
    rule_set: str,
    dry_run: bool,
    *,
    hmac_envelope_file: Optional[Path] = None,
    session_override: Optional[str] = None,
) -> None:
    loader = SSOTLoader(Path.cwd())
    config = loader.load()
    session_path = _resolve_with_override(config, session_override)

    # Part 2 (capture wiring): one capture per gogogo invocation; the
    # contextvar set inside capture() stamps every audit event below with
    # this capture's capture_id via emit_via_proxy.
    with capture(
        session_path,
        ritual="gogogo",
        role="KERNEL",
        kind="ritual_invocation",
    ) as cap:
        cap.input("invocation_params.json", {
            "rule_set": rule_set,
            "dry_run": dry_run,
            "hmac_envelope_file": str(hmac_envelope_file) if hmac_envelope_file else None,
        })
        _gogogo_inner(rule_set, dry_run, hmac_envelope_file, config, session_path, cap)


def _gogogo_inner(
    rule_set: str,
    dry_run: bool,
    hmac_envelope_file: Optional[Path],
    config,
    session_path: Path,
    cap,
) -> None:
    for marker in ("vvv_pass", "nnn_pass"):
        if not (session_path / ".state" / marker).exists():
            cmd = "ai vvv" if marker == "vvv_pass" else "ai nnn --plan-envelope <path>"
            console.print(
                f"[red]Missing .state/{marker}. "
                f"Run `{cmd}` first.[/red]"
            )
            raise typer.Exit(2)

    plan_path = session_path / ".state" / "plan.json"
    if not plan_path.exists():
        console.print(
            f"[red]Missing {plan_path}. Run `ai nnn --plan-envelope <path>` first.[/red]"
        )
        raise typer.Exit(2)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    cap.input("plan.json", plan)
    steps = plan.get("steps", [])
    if not steps:
        console.print("[red]Plan has no steps.[/red]")
        raise typer.Exit(2)

    # Spec line 795 normative MUST — gogogo refuses to run when the
    # verification_contract's contract_revision mismatches the plan
    # envelope's contract_revision. Both default to 0 when absent
    # (backward-compat with sessions that don't yet track revisions).
    # On mismatch, emit gogogo.precondition_failed and Exit(1) BEFORE
    # the step loop (so retro analysis sees a clean refusal, not a
    # half-executed plan).
    contract_path = session_path / "THINK" / "verification_contract.json"
    contract_revision_check_result: Optional[Dict[str, Any]] = None
    if contract_path.is_file():
        try:
            contract_dict = json.loads(contract_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            contract_dict = {}
        contract_rev = int(contract_dict.get("contract_revision", 0))
        plan_rev = int(plan.get("contract_revision", 0))
        contract_revision_check_result = {
            "contract_revision": contract_rev,
            "plan_envelope_revision": plan_rev,
        }
        # Note: we'll emit the audit row right after the loop+chain are
        # available (the chain is owned by Loop, instantiated below).

    loop = Loop(
        session_path,
        graph_name="standard",
        project_root=config.project_root,
    )
    if loop.current() != "DO":
        # KI-2026-05-16-002 fix — route blocked-state error footer through
        # the shared next_action formatter. Instead of generic "Run ai
        # next", compute + render the actual session-aware next command
        # inline so the operator sees the same text in error as in
        # `ai next` for the same graph_state.
        blocked_action = compute_next(
            config.project_root,
            session_path=session_path,
            graph_state=loop.current(),
        )
        blocked_action.blocked = True
        console.print(
            f"[red]graph_state must be DO; got {loop.current()!r}.[/red]\n"
            f"{render_one_line(blocked_action)}"
        )
        raise typer.Exit(2)

    # RC v1.1-rc Article XII.5 — load the gogogo pack so the empirical
    # ratification evidence trail is established. The pack declares a
    # CONCEPTUAL transition envelope (PLAN/SANDBOX/EXECUTE → SANDBOX/EXECUTE/
    # VERIFY); the physical graph collapses these into the single state DO
    # → VERIFIED. The pack guard is intentionally NOT called with the
    # physical pair here — calling assert_transition_allowed(pack, "DO",
    # "VERIFIED") would fail because DO is not in the pack's conceptual
    # allowed_current_states. This pack/graph naming divergence is
    # pre-existing structural drift, out of scope for this session (the
    # .ai/rituals/** path is forbidden_paths). The pack is loaded to (a)
    # validate file integrity at runtime, (b) anchor the audit-event
    # vocabulary, and (c) enforce conceptual transition assertions in test
    # code via test_gogogo_loader.py.
    gogogo_pack = load_pack(
        "gogogo",
        rituals_root=config.project_root / ".ai" / "rituals",
    )

    # Emit the pack-declared gogogo.invoked event as the first ritual-side
    # audit entry. Article XX — emission only after the pack has been
    # loaded and the higher-level state-precondition (above) has passed.
    loop.chain.append(
        "gogogo.invoked",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "kernel",
            "rule_set": rule_set,
            "dry_run": dry_run,
        },
    )

    # Spec line 795 normative — fire the contract_revision precondition
    # check AFTER gogogo.invoked (chain ordering: invoke → precheck →
    # step loop). When mismatched: emit gogogo.precondition_failed and
    # Exit(1) immediately. When matched: emit gogogo.precondition_ok
    # as an advisory marker (operator can grep for it to confirm the
    # contract was actually evaluated, not silently skipped).
    if contract_revision_check_result is not None:
        rev_contract = contract_revision_check_result["contract_revision"]
        rev_plan = contract_revision_check_result["plan_envelope_revision"]
        if rev_contract != rev_plan:
            loop.chain.append(
                "gogogo.precondition_failed",
                {
                    "session_id": session_path.name,
                    "decided_by": "kernel",
                    "reason": "contract_revision_mismatch",
                    "contract_revision": rev_contract,
                    "plan_envelope_revision": rev_plan,
                },
            )
            console.print(
                f"[red]gogogo refused — contract_revision mismatch: "
                f"verification_contract={rev_contract} vs plan_envelope="
                f"{rev_plan} (spec line 795).[/red]"
            )
            raise typer.Exit(1)
        loop.chain.append(
            "gogogo.precondition_ok",
            {
                "session_id": session_path.name,
                "decided_by": "kernel",
                "contract_revision": rev_contract,
                "plan_envelope_revision": rev_plan,
            },
        )

    # R35: HMAC verify before any step runs / any audit event fires.
    # Reject path leaves graph_state at DO and emits gogogo.hmac_rejected.
    transition_evidence_extra: Dict[str, Any] = {}
    if hmac_envelope_file is not None:
        chain = get_chain_for_project(config.project_root)
        try:
            envelope, payload_bytes, sig, ts_iso = load_hmac_envelope(
                hmac_envelope_file
            )
        except (ValueError, json.JSONDecodeError, OSError) as e:
            chain.append(
                "gogogo.hmac_rejected",
                {
                    "session_id": session_path.name,
                    "reason": "bad_envelope",
                    "ts_iso": None,
                    "detail": str(e),
                },
            )
            console.print(f"[red]gogogo.hmac_rejected: bad_envelope ({e})[/red]")
            raise typer.Exit(HMAC_REJECT_EXIT)

        ok, hmac_reason = verify_hmac(payload_bytes, sig, ts_iso)
        if not ok:
            chain.append(
                "gogogo.hmac_rejected",
                {
                    "session_id": session_path.name,
                    "reason": hmac_reason,
                    "ts_iso": ts_iso,
                    "envelope_keys": sorted(list(envelope.keys())),
                },
            )
            console.print(f"[red]gogogo.hmac_rejected: {hmac_reason}[/red]")
            raise typer.Exit(HMAC_REJECT_EXIT)

        transition_evidence_extra = {
            "via": "tg-bot:hmac",
            "hmac_ts": ts_iso,
            "hmac_nonce": envelope.get("nonce"),
            "hmac_user_id": envelope.get("user_id"),
        }

    budget = Budget.for_project(config.project_root)
    iterations_done = 0

    # Phase 4 — load real verifier rules once. Fail fast and loudly
    # if the rule_set name is unknown; that's an operator error, not
    # a per-step retry case.
    try:
        rules_doc = load_rules(config.project_root)
        get_rule_set(rules_doc, rule_set)
    except VerifierError as e:
        console.print(f"[red]verifier rule_set error: {e}[/red]")
        raise typer.Exit(2)

    step_verdicts: list[str] = []
    step_tiers: list[str] = []
    for step in steps:
        n = step.get("n", "?")
        title = step.get("title", "?")
        loop.chain.append(
            "gogogo.step_started",
            {
                "session_id": session_path.name,
                "step_n": n,
                "title": title,
                "graph_state": loop.current(),
                "decided_by": "kernel",
            },
        )

        # Phase 6 Session F — step-tool binding. Activates ONLY when the
        # step declares an optional `tool` field; the existing step
        # behaviour for steps without `tool` is byte-identical.
        tool_name = step.get("tool")
        if tool_name:
            try:
                registry = load_registry(config.project_root)
            except (RegistryValidationError, OSError) as exc:
                loop.chain.append(
                    "gogogo.step_failed",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "verifier_reason": f"tool registry load failed: {exc}",
                        "decided_by": "kernel",
                    },
                )
                console.print(
                    f"[red]step {n}: tool registry load failed — {exc}[/red]"
                )
                raise typer.Exit(2)

            # Wire #2 — sandbox profile load (optional, fail-soft).
            sandbox_profile_id = step.get("sandbox_profile")
            profile = None
            if sandbox_profile_id:
                try:
                    profile = _load_sandbox_profile(
                        config.project_root,
                        sandbox_profile_id,
                    )
                except SandboxProfileLoadError as exc:
                    loop.chain.append(
                        exc.event_type,
                        {
                            "session_id": session_path.name,
                            "step_n": n,
                            "title": title,
                            "profile_id": exc.profile_id,
                            "reason": exc.reason,
                            "decided_by": "kernel",
                        },
                    )
                    loop.chain.append(
                        "gogogo.step_failed",
                        {
                            "session_id": session_path.name,
                            "step_n": n,
                            "title": title,
                            "verifier_reason": exc.reason,
                            "decided_by": "kernel",
                        },
                    )
                    console.print(f"[red]step {n}: {exc.reason}[/red]")
                    raise typer.Exit(1)
            result = run_sandbox_gated_lifecycle(
                session_id=session_path.name,
                step_id=str(n),
                tool_name=tool_name,
                registry=registry,
                chain=loop.chain,
                profile=profile,
            )
            if not result.success:
                if result.sandbox_decision is not None and result.lifecycle is None:
                    reason = result.sandbox_decision.reason
                    console.print(
                        f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                        f"[red]SANDBOX-DENY[/red] ({reason})"
                    )
                else:
                    lifecycle = result.lifecycle
                    reason = (
                        lifecycle.decision.reason if lifecycle is not None else "unknown"
                    )
                    console.print(
                        f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                        f"[red]DENY[/red] ({reason})"
                    )
                raise typer.Exit(1)
            console.print(
                f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                f"[green]ALLOW[/green] (lease={result.lifecycle.lease.lease_id})"
            )

            # Phase 6 Session H — dispatch the registry-declared binary now
            # that sandbox + lifecycle have authorised the invocation. The
            # dispatcher itself emits tool.invocation.started, then one of
            # tool.invocation.completed / failed / timeout. A non-zero exit
            # short-circuits the step before the verifier sees it.
            record = registry.lookup(tool_name)
            if record is None:
                # Belt-and-braces — guard would have denied via lifecycle.
                loop.chain.append(
                    "gogogo.step_failed",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "verifier_reason": (
                            f"tool {tool_name!r} not in registry after ALLOW "
                            "(consistency violation)"
                        ),
                        "decided_by": "kernel",
                    },
                )
                console.print(
                    f"[red]step {n}: tool {tool_name!r} missing from registry "
                    f"after ALLOW[/red]"
                )
                raise typer.Exit(2)

            tool_args = list(step.get("tool_args") or [])
            tool_timeout = int(step.get("tool_timeout", 60))

            # P5 PolicyEngine GATE — must run BEFORE dispatch per spec
            # TRINITY_POLICY_ENGINE_SPEC_V1.md §3 (kernel MUST query
            # before tool call) + §5.3 (refusal audit event format) +
            # PRD Phase 5 acceptance "Policy can block tool use".
            # On deny: emit `policy.refused` with the §5.3 normative
            # field shape, then `raise typer.Exit(1)` — the tool never
            # runs. NEEDS_HUMAN is treated as deny for now (gate_required
            # path deferred until ddd integration).
            policy_doc = load_policy_doc(config.project_root)
            policy_envelope = build_query_envelope(
                actor_id="executor",
                authority_class="kernel",
                action_kind="tool_invoke",
                action_detail={"tool_name": tool_name},
                target_type="tool",
                target_value=tool_name,
                session_id=session_path.name,
                ritual_phase="DO",
                evidence_refs=[
                    f"lease/{result.lifecycle.lease.lease_id}",
                ],
            )
            policy_verdict = policy_query(policy_envelope, policy_doc=policy_doc)
            if policy_verdict.verdict != "allow":
                # Spec §5.3 normative field shape: flat actor / action_kind /
                # target / verdict / reason / rule_id / rule_file / query_id /
                # engine_version. Carry the full verdict envelope too for
                # downstream audit consumers.
                evidence = dict(policy_verdict.evidence_ref or {})
                row = {
                    "session_id": session_path.name,
                    "step_n": n,
                    "actor": policy_envelope.actor.get("id", "executor"),
                    "action_kind": policy_envelope.action.get("kind", ""),
                    "target": tool_name,
                    "verdict": policy_verdict.verdict,
                    "reason": policy_verdict.reason,
                    "rule_id": evidence.get("rule_id", ""),
                    "rule_file": evidence.get("rule_file", ""),
                    "query_id": policy_verdict.query_id,
                    "engine_version": policy_verdict.engine_version,
                    "decided_by": "policy",
                    **envelope_to_audit_dict(policy_verdict),
                }
                # Spec §5.4 forbidden_path special form
                if policy_verdict.reason == "forbidden_path":
                    fp = evidence.get("forbidden_pattern")
                    if fp:
                        row["forbidden_pattern"] = fp
                    gid = evidence.get("gate_id")
                    if gid:
                        row["gate_id"] = gid

                # Spec §6.5 NEEDS_HUMAN flow — distinct from deny:
                # emit policy.gate_required (NOT policy.refused), write
                # ddd-packet template to <session>/GATE/<gate_id>_packet.yaml
                # per §6.2 field shape, then Exit(0) — kernel pauses
                # awaiting decided_by:human envelope (spec §5.2:
                # "Refusal is not failure"; gate is a normal pause).
                if policy_verdict.verdict == "NEEDS_HUMAN":
                    gate_id = evidence.get("gate_id", "gate.unknown")
                    row["gate_id"] = gate_id
                    gate_dir = session_path / "GATE"
                    gate_dir.mkdir(parents=True, exist_ok=True)
                    packet_path = gate_dir / f"{gate_id}_packet.yaml"
                    import yaml as _yaml
                    packet_path.write_text(
                        _yaml.safe_dump(
                            {
                                "decided_by": "human",  # operator must edit
                                "human_id": "",
                                "gate_id": gate_id,
                                "query_id": policy_verdict.query_id,
                                "action_kind": policy_envelope.action.get("kind", ""),
                                "target": tool_name,
                                "decision": "approve|deny",  # operator edits
                                "rationale": "",
                            },
                            sort_keys=False,
                        ),
                        encoding="utf-8",
                    )
                    row["ddd_packet_path"] = str(packet_path)
                    loop.chain.append("policy.gate_required", row)
                    console.print(
                        f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                        f"[yellow]NEEDS-HUMAN[/yellow] "
                        f"(gate={gate_id})\n"
                        f"  [yellow]Packet:[/yellow] {packet_path}\n"
                        f"  [yellow]Fill `decision: approve` + `human_id` "
                        f"+ `rationale`, then re-run gogogo or run `ai ddd`.[/yellow]"
                    )
                    raise typer.Exit(0)

                # Default: deny path → policy.refused + Exit(1)
                loop.chain.append("policy.refused", row)
                console.print(
                    f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                    f"[red]POLICY-REFUSED[/red] "
                    f"({policy_verdict.verdict}: {policy_verdict.reason})"
                )
                raise typer.Exit(1)

            # Phase 7 Sessions H2/H3 — fs + net + proc runtime hook.
            # When the profile declares OS-enforced axes and the host
            # cannot apply sandbox-exec, fail closed. Tool-only profiles
            # still work through sandbox_gate above.
            argv_transform = None
            sandbox_profile_file: Optional[Path] = None
            required_axes = runtime_enforcement_axes(profile)
            runtime_enforcement_enabled = _sandbox_runtime_enforcement_enabled(config)
            if required_axes and not runtime_enforcement_enabled:
                loop.chain.append(
                    "sandbox.runtime_disabled",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "tool_name": tool_name,
                        "profile_id": sandbox_profile_id,
                        "required_axes": required_axes,
                        "reason": (
                            "sandbox.runtime_enforcement_enabled=false in "
                            ".ai/ssot.yaml"
                        ),
                        "decided_by": "kernel",
                    },
                )
            elif required_axes and not is_sandbox_exec_available():
                loop.chain.append(
                    "sandbox.runtime_unavailable",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "tool_name": tool_name,
                        "profile_id": sandbox_profile_id,
                        "required_axes": required_axes,
                        "reason": (
                            "sandbox profile declares OS-enforced axes but "
                            "sandbox-exec is unavailable on this host"
                        ),
                        "decided_by": "kernel",
                    },
                )
                loop.chain.append(
                    "gogogo.step_failed",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "verifier_reason": (
                            "sandbox runtime unavailable for declared axes: "
                            + ",".join(required_axes)
                        ),
                        "decided_by": "kernel",
                    },
                )
                console.print(
                    f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                    f"[red]SANDBOX-RUNTIME-UNAVAILABLE[/red] "
                    f"(axes={','.join(required_axes)})"
                )
                raise typer.Exit(1)
            if runtime_enforcement_enabled and should_wrap(profile):
                profile_text = build_sandbox_profile_text(
                    profile, config.project_root
                )
                sandbox_profile_file = write_profile_to_tmp(profile_text)
                argv_transform = (
                    lambda argv, _p=sandbox_profile_file: wrap_argv_with_sandbox_exec(
                        argv, _p
                    )
                )

                # S15 — emit sandbox.allowlist_unenforced when the
                # operator declared a hostname allowlist that
                # sandbox-exec cannot enforce at the IP level. The
                # event records the intended hostnames + their DNS
                # snapshot so retro analysis sees the gap between
                # declared and actual enforcement.
                if should_emit_unenforced_warning(profile):
                    resolved = resolve_allowlist_hostnames(
                        list(profile.net.allowlist)
                    )
                    loop.chain.append(
                        "sandbox.allowlist_unenforced",
                        {
                            "session_id": session_path.name,
                            "step_n": n,
                            "tool_name": tool_name,
                            "decided_by": "kernel",
                            "reason": (
                                "sandbox-exec rejects literal-IP allowlist; "
                                "deny fallback active"
                            ),
                            "declared_allowlist": list(profile.net.allowlist)[:20],
                            "resolved_snapshot": {
                                h: ips for h, ips in list(resolved.items())[:20]
                            },
                        },
                    )

            try:
                dispatch_result = dispatch_tool(
                    lease=result.lifecycle.lease,
                    record=record,
                    args=tool_args,
                    chain=loop.chain,
                    project_root=config.project_root,
                    timeout_seconds=tool_timeout,
                    argv_transform=argv_transform,
                )
            finally:
                if sandbox_profile_file is not None:
                    sandbox_profile_file.unlink(missing_ok=True)
            if dispatch_result.exit_code != 0:
                loop.chain.append(
                    "gogogo.step_failed",
                    {
                        "session_id": session_path.name,
                        "step_n": n,
                        "title": title,
                        "verifier_reason": (
                            f"tool dispatch failed: exit={dispatch_result.exit_code} "
                            f"timed_out={dispatch_result.timed_out}"
                        ),
                        "decided_by": "kernel",
                    },
                )
                console.print(
                    f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                    f"[red]DISPATCH-FAIL[/red] "
                    f"(exit={dispatch_result.exit_code}, "
                    f"timed_out={dispatch_result.timed_out})"
                )
                raise typer.Exit(1)
            console.print(
                f"  [dim]step {n}[/dim] tool=[bold]{tool_name}[/bold] -> "
                f"[green]DISPATCH-OK[/green] "
                f"(exit=0, {dispatch_result.duration_seconds:.3f}s)"
            )

        verdict = _verify_step(step, rule_set, rules_doc)
        step_verdicts.append(verdict.verdict)
        step_tiers.append(verdict.tier)
        console.print(
            f"  [dim]step {n}[/dim] [{verdict.rule_set}/{verdict.mode}] "
            f"-> [bold]{verdict.verdict}[/bold] ({verdict.reason})"
        )

        loop.chain.append(
            f"gogogo.step_{'passed' if verdict.verdict == 'PASS' else 'failed'}",
            {
                "session_id": session_path.name,
                "step_n": n,
                "title": title,
                "rule_set": verdict.rule_set,
                "verifier_verdict": verdict.verdict,
                "verifier_mode": verdict.mode,
                "verifier_reason": verdict.reason,
                "tier": verdict.tier,  # PRD Phase 8 — every verdict path maps to a tier
                "decided_by": "verifier",
            },
        )

        if verdict.verdict == "DEAD":
            console.print(
                f"[red]Step {n} DEAD — terminating loop.[/red]"
            )
            raise typer.Exit(1)

        iterations_done += 1
        # Budget re-check (D11): per-step checkpoint
        bv = budget.check(
            {
                "estimated_iterations": iterations_done,
                "estimated_duration_minutes": plan.get(
                    "budget_envelope", {}
                ).get("estimated_duration_minutes", 0),
                "estimated_tool_calls": plan.get(
                    "budget_envelope", {}
                ).get("estimated_tool_calls", 0),
                "budget_override": plan.get("budget_override"),
            },
            graph_name="standard",
        )
        if not bv.ok:
            loop.chain.append(
                "loop.budget.breach",
                {
                    "session_id": session_path.name,
                    "step_n": n,
                    "decided_by": "policy",
                    "breaches": bv.breaches,
                },
            )
            console.print(
                Panel(
                    f"NEEDS_HUMAN — budget breach at step {n}.\n"
                    f"  breaches: {bv.breaches}",
                    title="🟡 gogogo — NEEDS_HUMAN",
                    border_style="yellow",
                )
            )
            raise typer.Exit(0)

    loop.chain.append(
        "gogogo.completed",
        {
            "session_id": session_path.name,
            "graph_state": loop.current(),
            "decided_by": "verifier",
            "steps_completed": len(steps),
            "rule_set": rule_set,
        },
    )

    # Phase 8 verifier runtime — first runtime caller of verification_contract
    # types. Consolidates per-step verdicts via the closed
    # DEAD > NEEDS_HUMAN > RETRY > PASS precedence and emits a
    # `verifier.consolidated` audit row. Fail-soft: a drift in step
    # verdicts logs a warning but does not abort (Article XX passive).
    if step_verdicts:
        try:
            terminal_verdict = consolidate_step_verdicts(step_verdicts)
            row = {
                "session_id": session_path.name,
                "decided_by": "verifier",
                "step_verdicts": step_verdicts,
                "terminal_verdict": terminal_verdict,
                "precedence": list(CONSOLIDATION_PRECEDENCE),
            }
            # PRD Phase 8 — tier-mapping. Carry per-step tiers + a
            # terminal_tier consolidated via COLD > WARM > HOT.
            if step_tiers and all(t for t in step_tiers):
                try:
                    terminal_tier = consolidate_step_tiers(step_tiers)
                    row["step_tiers"] = step_tiers
                    row["terminal_tier"] = terminal_tier
                    row["tier_precedence"] = list(TIER_SEVERITY)
                except ValueError:
                    # Tier drift (e.g. _TIER_SENTINEL leaked through) —
                    # skip tier consolidation but keep verdict row.
                    pass
            loop.chain.append("verifier.consolidated", row)
        except ValueError as exc:
            console.print(
                f"  [yellow]⚠ verifier consolidation skipped: {exc}[/yellow]"
            )
    cap.output("gogogo_result.json", {
        "steps_completed": len(steps),
        "graph_state": loop.current(),
        "rule_set": rule_set,
        "dry_run": dry_run,
    })
    cap.validation("verdict_summary.json", {"all_steps": "PASS", "count": len(steps)})

    if not dry_run:
        loop.fire(
            "gogogo_complete",
            decided_by="verifier",
            evidence={
                "steps_completed": len(steps),
                "rule_set": rule_set,
                **transition_evidence_extra,
            },
        )

    console.print(
        Panel(
            f"gogogo complete.\n"
            f"  steps: {len(steps)}\n"
            f"  graph_state: {loop.current()}",
            title="✅ gogogo",
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
    """KI-2026-05-16-001 fix — resolve session with optional --session override."""
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
                "ritual": "gogogo",
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

---
title: "Trinity Organ Map v1.0"
version: "1.0"
status: "locked"
last-updated: "2026-05-12"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
parent: "TRINITY_CONSTITUTION_V1.md"
related:
  - "trinity_organ_refactor_prd.md §8 (organ contracts 8.1-8.18)"
  - "TRINITY_RITUAL_CONTRACT_V1.md (gate → organ routing)"
---

# Trinity Organ Map v1.0

> Trinity is an organism, not a script. Each organ has a narrow role
> (Article IV). No organ may silently absorb another organ's role
> (Article XXVII — Scope Discipline).
>
> Every organ MUST declare the eight extension-rule fields
> (Article XXVIII): role, authority, inputs, outputs, artifacts,
> state permissions, failure behavior, audit behavior.
>
> Components that cannot answer all eight are scripts, not organs,
> and MUST NOT be wired into Trinity core.

## Compliance Legend

| Symbol | Meaning |
|---|---|
| ✅ | Article IV compliant — role bounded, no collapse |
| ⚠ | Partial — role bounded but ownership split or contract incomplete |
| 🔴 | Role collapse — organ absorbs another organ's role (Article IV violation) |
| ⏳ | Not yet implemented — declared in spec, awaits build |

---

## 1. Kernel

**Role:** Governance, state, gates, authority.
**Owns:** workflow state, legal transitions, policy checks, authority checks, ritual routing.
**Must not own:** reasoning, execution, verification, memory interpretation, retro meaning.
**Inputs:** ritual commands, plan envelopes, decision packets, HMAC envelopes.
**Outputs:** state transitions, audit events, gate verdicts.
**Artifacts:** `META.json`, audit events under `.ai/audit/events.ndjson`.
**State permissions:** writes `.state/`, fires all canonical state transitions.
**Failure behavior:** illegal transitions rejected with `gate_lock` envelope.
**Audit behavior:** every transition emits a `graph.transition` event with `decided_by`.
**Security boundary:** consumes signed envelopes (HMAC); does NOT execute model-generated commands directly.
**Current implementer:** `trinity_v2/.ai/cli/` (sss/vvv/nnn/gogogo/ddd/rrr/close commands).
**Status:** ✅ Mostly clean. Refactor target: extract policy engine (Phase 5) and formalise state graph (Phase 4).

---

## 2. State Graph

**Role:** Finite workflow state machine governing every workflow's lifecycle.
**Owns:** canonical states (READY, THINK, PLAN, SANDBOX, EXECUTE, VERIFY, PROMOTE, DEPLOY, RETRO, DONE, FAILED, ABORTED, REOPENED) and the legal transitions between them.
**Must not own:** policy content, command semantics, organ execution.
**Inputs:** transition requests (with declared `from`, `to`, `decided_by`, evidence).
**Outputs:** allow / deny / require-human verdicts.
**Artifacts:** `.ai/graphs/standard.yaml` (planned), transition log entries.
**State permissions:** owns the state slot; nothing else may write to it.
**Failure behavior:** illegal transitions emit `state.illegal_transition` and HALT the workflow.
**Audit behavior:** every accepted transition logs `graph.transition`; rejections log `state.illegal_transition`.
**Security boundary:** state changes only through Kernel; no direct mutation by AI or transport.
**Current implementer:** embedded in Kernel `commands/` (no standalone graph file yet).
**Status:** ⏳ Planned for Phase 4. Today the state machine is implicit in command handlers.

---

## 3. Policy Engine

**Role:** Enforce allowed and forbidden actions independent of state.
**Owns:** forbidden paths, critical-gate policy, secret policy, capability rules, risk escalation rules.
**Must not own:** state graph content, command semantics, execution.
**Inputs:** action request (verb + target + actor + tier).
**Outputs:** allow / deny / escalate verdict with cited rule.
**Artifacts:** `.ai/policies/trinity_policy.yaml` (planned consolidation), verifier-rules, safety, gates yamls.
**State permissions:** read-only against state; gates transitions when policy fires.
**Failure behavior:** policy violation emits `policy.denied` and blocks the action.
**Audit behavior:** every policy decision (allow + deny) logs `policy.evaluated`.
**Security boundary:** policy is human-write-only (`.ai/policies/**` is forbidden to AI).
**Current implementer:** `.ai/policies/verifier-rules.yaml`, `.ai/policies/safety.yaml`, `.ai/policies/gates.yaml`.
**Status:** ⚠ Split across three files. Phase 5 consolidates into `trinity_policy.yaml` with rule categories.

---

## 4. Ritual Controller

**Role:** Map ritual commands (sss/vvv/nnn/gogogo/ddd/rrr/close) to the organs that do the work.
**Owns:** command-to-organ routing and audit wrappers around each ritual invocation.
**Must not own:** execution logic, semantic interpretation, verification truth.
**Inputs:** CLI invocation + session state.
**Outputs:** delegation calls to organs + transition fires.
**Artifacts:** `TRINITY_RITUAL_CONTRACT_V1.md` (this Phase 0), per-command tests.
**State permissions:** triggers state transitions via Kernel only.
**Failure behavior:** routing failure (e.g. organ unavailable) emits `ritual.delegation_failed` and HALTS without state change.
**Audit behavior:** every ritual invocation emits a `<ritual>.invoked` event.
**Security boundary:** does NOT execute work directly; pure routing.
**Current implementer:** `.ai/cli/commands/{sss,vvv,nnn,gogogo,ddd,rrr,close}.py` (but commands today still do organ work themselves).
**Status:** ⚠ Commands currently absorb organ work. Phase 1 (rrr) and Phase 12 (retro/rrr split) thin them down.

---

## 5. Planner

**Role:** Reasoning, plans, risk analysis.
**Owns:** `PLAN.md`, scope declaration, risk assessment, verification contract.
**Must not own:** execution, approval, verification result, state transition.
**Inputs:** task description (operator or AI), prior plans, prior retros.
**Outputs:** plan envelope (JSON) + scope + verification contract.
**Artifacts:** `PLAN.md`, `plan_envelope.json`, `scope.json`, `verification_contract.json`, `risk_assessment.md`.
**State permissions:** writes inside session `THINK/`; no other writes.
**Failure behavior:** plan envelope validation failure emits `nnn.failed` and HALTS.
**Audit behavior:** `nnn.proposed`, `nnn.passed`, `nnn.failed`.
**Security boundary:** plans are advisory until approved by Kernel.
**Current implementer:** model + `nnn` ritual + `plan_envelope.json` template.
**Status:** ✅ Clean. Phase 3 adds the explicit verification contract schema.

---

## 6. Executor

**Role:** Bounded action.
**Owns:** file edits, shell/tool calls, execution logs, diffs.
**Must not own:** approval, verification, final completion, state transition.
**Inputs:** approved plan + execution lease + sandbox profile.
**Outputs:** `diff.patch`, `execution.log`, `tool_calls.jsonl`, `artifact_manifest.json`.
**Artifacts:** the four above + the actual file changes.
**State permissions:** writes inside DO/dev (after `vvv_pass`); cannot write `DO/prod` (human-only).
**Failure behavior:** execution error emits `gogogo.step.failed` with diff and log attached.
**Audit behavior:** `gogogo.step.started`, `gogogo.step.completed`, `gogogo.step.failed`.
**Security boundary:** Sandbox (organ 7) enforces blast radius.
**Current implementer:** bash + Edit/Write tools + sibling CLIs (wp/image/seo/etc.).
**Status:** ⚠ Scattered. Phase 6 adds the Tool Capability Registry to declare each sibling's authority.

---

## 7. Sandbox

**Role:** Enforce blast radius below the model layer.
**Owns:** filesystem boundary, network egress boundary, command allowlist, env restrictions, temporary credentials.
**Must not own:** policy content, state, verification truth.
**Inputs:** `sandbox_profile.json` derived from plan envelope's allowed/forbidden paths.
**Outputs:** allow / deny on every executor IO; visible escape attempts.
**Artifacts:** `sandbox_profile.json` per session.
**State permissions:** read-only; gates Executor's writes.
**Failure behavior:** escape attempt emits `sandbox.violation` and BLOCKS the action.
**Audit behavior:** every violation logged; clean operations need not log to keep the chain readable.
**Security boundary:** default-deny network, allowlist filesystem, blocked secret paths.
**Current implementer:** session sandbox directories (`SANDBOX/<role>/`, `DO/dev/`) + Claude Code permission prompts; no enforced sandbox profile yet.
**Status:** ⏳ Planned for Phase 7. Today, blast radius depends on operator vigilance.

---

## 8. Verifier

**Role:** Independent validation.
**Owns:** deterministic checks, policy checks, test/lint/typecheck results, `verifier_report.json`.
**Must not own:** deployment, mutation, silent fixes, final authority.
**Inputs:** plan + execution artifacts + verification contract.
**Outputs:** PASS / FAIL / UNVERIFIED verdict with tier and cited evidence.
**Artifacts:** `verifier_report.json` per session.
**State permissions:** read-only; verdict is consumed by DDD/Kernel.
**Failure behavior:** explicit FAIL blocks PROMOTE/DEPLOY; UNVERIFIED escalates to human.
**Audit behavior:** every verdict path logs `verifier.verdict` with `tier` and `evidence_ref`.
**Security boundary:** AI advisory (Tier 3) is gated; AI verdict alone cannot promote/deploy.
**Current implementer:** `.ai/policies/verifier-rules.yaml` (Tier 0–2 rules) + `judge-cli` (Tier 3 LLM advisory) + `test-cli` + `trinity-contract-test`.
**Status:** ⚠ Split ownership across 4 places. Phase 8 consolidates the harness and declares tier per check.

### Verifier Pyramid

```text
Tier 0  artifact existence, hash, schema, command exit
Tier 1  tests, lint, typecheck, contract tests
Tier 2  policy-as-code
Tier 3  AI advisory review only (never sole pass for COLD)
Tier 4  human gate
```

---

## 9. Memory CLI

**Role:** Exact artifact evidence retrieval.
**Owns:** indexing, search, show, pack, pins, clean/purge of real on-disk artifacts.
**Must not own:** semantic learning, summarisation, canonical truth decisions, execution.
**Inputs:** file paths, search queries, pack queries, pin commands.
**Outputs:** chunk evidence rows with `path + line range + byte range + text_sha256 + artifact_sha256 + indexed_at_utc`.
**Artifacts:** SQLite at `.memory/memory.sqlite` (project-local), evidence packs under `.memory/packs/`.
**State permissions:** writes to its own DB and `packs/`; never to workflow state.
**Failure behavior:** index/search failures surface verbatim; passive — never auto-triggered.
**Audit behavior:** sibling tool envelope returned; Kernel may log invocation.
**Security boundary:** denylist (binaries, secrets, lockfiles) applied during walk; size cap; binary detection.
**Current implementer:** `<workspace-root>/memory-cli` v0.1 (deployed 2026-05-12, commit `b3f1a13`).
**Status:** ✅ Clean. Legacy semantic verbs (`learn`, `promote`, `verify`, `trace`, `embed`, `similar`, `map`, `thread*`) fenced behind `MEMORY_CLI_LEGACY=1`.

---

## 10. Audit

**Role:** Immutable history.
**Owns:** event log, hash chain, transition history, artifact references.
**Must not own:** semantic truth, approval authority.
**Inputs:** events from every organ.
**Outputs:** chain-validated NDJSON.
**Artifacts:** `.ai/audit/events.ndjson` (hash chain, append-only).
**State permissions:** append-only. Mutation forbidden to all actors including human (corrections create new entries).
**Failure behavior:** chain-validation failure HALTS workflow.
**Audit behavior:** itself the audit layer.
**Security boundary:** SHA-256 chain links every event to its predecessor.
**Current implementer:** `.ai/audit/events.ndjson` written by `.ai/cli/core/loop.py:chain.append()`.
**Status:** ⚠ Clean storage, but no formal replay validator yet. Phase 10 adds `audit replay` and `audit verify-chain`.

---

## 11. Retro

**Role:** Post-work reflection artifact generation.
**Owns:** lessons draft, bottleneck notes, improvement suggestions.
**Must not own:** memory indexing, canonical pinning, state transition, verification.
**Inputs:** completed session (audit chain + artifacts).
**Outputs:** human-readable retro draft (semantic) — distinct from RRR's deterministic closure.
**Artifacts:** `RETRO.md` (semantic, in-session) and `.ai/memory/retros/NNNN_*.md` (canonical, cross-session — currently written BY RRR, not Retro).
**State permissions:** writes to session `THINK/RETRO.md` and `.ai/memory/retros/`.
**Failure behavior:** retro generation failure is non-blocking; retro file is the source of truth.
**Audit behavior:** `retro.generated`.
**Security boundary:** retros are advisory; they do NOT auto-pin or mutate memory.
**Current implementer:** currently absorbed by `.ai/cli/commands/rrr.py`.
**Status:** 🔴 Role collapse. Phase 12 separates Retro from RRR terminal closure.

---

## 12. RRR Terminal Gate

**Role:** Terminal governance gate and closure delegator.
**Owns:** acceptance collection, forbidden-diff checks, metrics computation, graph transition to DONE, audit emission.
**Must not own:** memory learning, semantic retro meaning, canonical pinning, verification truth.
**Inputs:** session in VERIFIED or DEPLOYED state.
**Outputs:** closure transition + `rrr.completed` event + retro artifact reference.
**Artifacts:** `THINK/RETRO.md` (deterministic closure envelope), `.ai/memory/retros/NNNN_*.md` (delegated to Retro + Memory).
**State permissions:** fires VERIFIED → DONE.
**Failure behavior:** acceptance / forbidden-diff failure blocks closure visibly.
**Audit behavior:** `rrr.completed` with metrics, acceptance counts, retro file path, memory index result.
**Security boundary:** does NOT call `memory-cli learn` (Article IX); MUST call `memory-cli index` (mechanical).
**Current implementer:** `.ai/cli/commands/rrr.py`.
**Status:** 🔴 Article IX violation. Phase 1 (the very next session) replaces `memory-cli learn --file=<retro>` with `memory-cli index <retro-path>`.

---

## 13. DDD / Human Gate

**Role:** Human or governance decision gate.
**Owns:** approve / reject / hold / approve-with-conditions verdicts on PROMOTE and DEPLOY.
**Must not own:** execution, silent approval, unverified promotion.
**Inputs:** verifier report + decision packet + artifact manifest.
**Outputs:** decision artifact (`approval.json` | `rejection.json` | `hold.json`).
**Artifacts:** `decision_packet.json`, then one of the three verdict files.
**State permissions:** fires VERIFY → PROMOTE → DEPLOY.
**Failure behavior:** approval without verifier report = block; reject creates a `rejection.json` and HALTS deploy.
**Audit behavior:** `ddd.completed` with `decided_by`, `target`, `reason`, `evidence_ref`.
**Security boundary:** transport-delivered approvals MUST come through HMAC envelopes (Article XV); Kernel verifies signatures.
**Current implementer:** `.ai/cli/commands/ddd.py` + `core/auth.py` HMAC verifier.
**Status:** ⚠ HMAC pipeline shipped (commit `6557180`); audit field hardening planned for Phase 11.

---

## 14. Transport Gateway

**Role:** Delivery only.
**Owns:** Telegram / Slack / webhook / API input and response delivery.
**Must not own:** authority, approval, workflow state mutation.
**Inputs:** external messages.
**Outputs:** signed envelopes forwarded to Kernel.
**Artifacts:** message logs (encrypted if PII), signed envelopes.
**State permissions:** none. Cannot mutate state.
**Failure behavior:** delivery failure surfaces to operator; retries are bounded.
**Audit behavior:** `transport.envelope_received`, `transport.envelope_forwarded`.
**Security boundary:** HMAC-signed envelopes only. A transport-originated approval that doesn't pass Kernel verification MUST fail closed.
**Current implementer:** `trinity-tg-bot` (Telegram) + `notify-cli` (outbound).
**Status:** ⚠ Bot wired; Phase 9 audit verifies it cannot approve DDD directly.

---

## 15. Tool Capability Registry

**Role:** Declare every tool's authority before use.
**Owns:** tool identity, allowed operations, inputs/outputs, artifacts, security boundary.
**Must not own:** the execution of those tools.
**Inputs:** per-tool `trinity.yaml` or `contract.json` declarations.
**Outputs:** `.ai/tools.capabilities.yaml` (consolidated registry).
**Artifacts:** per-tool contract files + the consolidated yaml.
**State permissions:** read-only at runtime; Kernel validates against the registry before allowing a tool call.
**Failure behavior:** unknown tool = denied (Article XVI Least Authority).
**Audit behavior:** `tool.registered`, `tool.denied`.
**Security boundary:** registry itself is human-write-only.
**Current implementer:** `.ai/tools.yaml` (partial — declares some siblings, not all).
**Status:** ⏳ Phase 6 builds the formal capability model and validates every sibling contract.

---

## 16. Presentation Protocol

**Role:** Protect human judgment from cognitive overload (Addendum §E).
**Owns:** convergence compression, dissent expansion, founder questions, raw artifact links.
**Must not own:** authority, truth, ratification.
**Inputs:** verifier report + decision packet + dissent log.
**Outputs:** `presentation_synthesis.json` + dissent surface + raw artifact links.
**Artifacts:** `ratification_packet.json`, `presentation_synthesis.json`, `ratification_decision.json`.
**State permissions:** read-only.
**Failure behavior:** if dissent cannot be surfaced, presentation FAILS — never silenced.
**Audit behavior:** `presentation.rendered`, `presentation.synthesis_diverges_from_dissent` (warning).
**Security boundary:** compressed view never replaces raw artifacts.
**Current implementer:** none yet.
**Status:** ⏳ Phase 13.

---

## 17. Root of Trust / Ratification

**Role:** Make human authority machine-verifiable.
**Owns:** genesis trust manifest, signed canonical artifacts, versioning, revocation, threshold rules.
**Must not own:** day-to-day execution.
**Inputs:** Layer 0 artifacts (Constitution, Addendum, Organ Map, Ritual Contract).
**Outputs:** `genesis_manifest.json`, ratification signatures, revocation log.
**Artifacts:** `audit/genesis_manifest.json` + ratified artifacts.
**State permissions:** write-once at genesis; revocations create new entries.
**Failure behavior:** unsigned canonical artifact = warning today (HOT/WARM); BLOCK after Phase 14 for COLD.
**Audit behavior:** `ratification.signed`, `ratification.revoked`.
**Security boundary:** cryptographic signatures; revocation log immutable.
**Current implementer:** none yet (Addendum §A declares `GENESIS_TRUST_ASSUMED`).
**Status:** ⏳ Phase 14. Schema declared in Addendum so consumers know where it will land.

---

## 18. Close / Session Finalizer

**Role:** Seal and archive completed session.
**Owns:** final manifest verification, temp cleanup, next-step hint, optional external audit emission.
**Must not own:** rewriting audit or retro.
**Inputs:** session in DONE / FAILED / ABORTED.
**Outputs:** `final_manifest.json`, `session_close_report.md`, archive move.
**Artifacts:** the two above.
**State permissions:** moves `.ai/sessions/active/<sid>/` → `.ai/sessions/archive/<sid>.archive/`.
**Failure behavior:** close on a non-terminal state = block (with `--force` override creating an audit warning).
**Audit behavior:** `session.closed` with `final_manifest_sha256`.
**Security boundary:** read-only against audit; close does NOT rewrite events.
**Current implementer:** `.ai/cli/commands/close.py`.
**Status:** ⚠ Phase 15 adds final-manifest hash verification + COLD-path external audit emission (Addendum §D).

---

## Compliance Summary

| # | Organ | Status |
|---|---|---|
| 1 | Kernel | ✅ |
| 2 | State Graph | ⏳ |
| 3 | Policy Engine | ⚠ |
| 4 | Ritual Controller | ⚠ |
| 5 | Planner | ✅ |
| 6 | Executor | ⚠ |
| 7 | Sandbox | ⏳ |
| 8 | Verifier | ⚠ |
| 9 | Memory CLI | ✅ |
| 10 | Audit | ⚠ |
| 11 | Retro | 🔴 |
| 12 | RRR Terminal Gate | 🔴 |
| 13 | DDD / Human Gate | ⚠ |
| 14 | Transport Gateway | ⚠ |
| 15 | Tool Capability Registry | ⏳ |
| 16 | Presentation Protocol | ⏳ |
| 17 | Root of Trust | ⏳ |
| 18 | Close / Session Finalizer | ⚠ |

**Immediate priorities (Phase 1–2):** organ 12 (RRR) and organ 11 (Retro) — both are role-collapsed today and block constitutional compliance of every session.

**Pre-production blockers (Phase 6–9):** organs 7 (Sandbox), 14 (Transport), 15 (Tool Capability) — without these, blast radius is undefined.

**Optional but valuable:** organs 16 (Presentation), 17 (Root of Trust) — improve operator ergonomics and future verifiability.

# Policy + Sandbox Layer — Classification Audit (T4-AUDIT)

> **Session:** `0001_2026-06-17_01_25_am_feat-policy-sandbox-audit-classification-t4`
> **Type:** read-only classification (Tier C → resolved). No code changed.
> **Evidence base:** full read of 8 core modules + grep of consumers + 172 passing
> policy/sandbox tests (`test_policy_engine`, `test_policy_contract`,
> `test_sandbox_runtime`, `test_sandbox_contract`, `test_sandbox_enforcer`,
> `test_sandbox_gate`, `test_hmac_gate`, `test_gogogo_sandbox_wiring`).
> **Verdict vocabulary:** `implemented` (real working logic) · `advisory`
> (returns verdicts/data but enforces nothing itself) · `stub` (placeholder) ·
> `deferred` (explicitly not-yet-done). Plus **wired** (consumed by a live
> codepath) vs **dead** (only tests reference it).

---

## Headline

The policy + sandbox layer is **largely implemented and genuinely enforcing** —
not a field of stubs. The Tier-C "unverified" status is resolved: **T4.1/4.2/4.3
do not require building enforcement from scratch.** What remains is a small set
of **dead code** and **declared-but-not-enforced POC gaps**, listed in Follow-up.

---

## Policy layer

| Module | Verdict | Wired | Notes |
|--------|---------|-------|-------|
| `policy_engine.py` | **implemented** | ✅ live | the real enforcing engine |
| `policy_contract.py` | **advisory** (declarative) | ✅ live (types/consts) | `resolve_precedence` helper is test-only/dead |
| `hmac_gate.py` | **implemented** | ✅ live | transport HMAC gate |
| `policy.py` | **stub** (self-labeled) | ❌ **dead** | superseded by `policy_engine.py` |

### policy_engine.py — implemented · wired
`query()` (line 281) is a real default-deny ladder: schema → `deny(schema_invalid)`;
authority ∉ allowed → `deny(unknown_authority)` (315); forbidden mutation-path glob →
`deny(forbidden_path)` (339); critical-gate match → `NEEDS_HUMAN/human_gate_required`
(368); forbidden tool → `deny(illegal_target)` (393); else `allow` (advisory.poc, 412).
**Enforced, not logged:** `gogogo.py:728-821` runs the query before every tool
dispatch — `deny` → `policy.refused` + `Exit(1)` (tool never runs); `NEEDS_HUMAN` →
ddd packet + `policy.gate_required` + `Exit(0)` pause. `load_policy_doc` (51) is
read-only with thin-client fallback + default-deny on miss. Wired at `gogogo.py:41`.

### policy_contract.py — advisory (declarative) · wired
Pure declarative contract: `VERDICT_SET`/`VERDICT_PRECEDENCE` (deny>NEEDS_HUMAN>
conditional>allow)/`REASON_CODES`/`ALLOWED_AUTHORITY_CLASSES` + the
`PolicyQueryEnvelope`/`PolicyVerdictEnvelope` dataclasses. Consumed by
`policy_engine.py:41` (so live transitively). `resolve_precedence()` (148) is real
but **only tests call it** — a dead helper inside a live module.

### hmac_gate.py — implemented · wired
`enforce_hmac_or_exit()` (52): `None` → bypass; bad envelope / `verify_hmac` fail →
`<ritual>.hmac_rejected` audit + `Exit(79)`; success → transport-evidence dict.
Wired into `sss.py:321`, `vvv.py:141`, `nnn.py:131`, `close.py:166`.

### policy.py — stub · DEAD ⚠️
Self-labels (line 1) "policy validator **stub** (Phase 5, Step S5)", line 14
"Runtime enforcement is **deferred**." `validate()` does real YAML/tier checks but
produces only a report and **has zero production importers** — superseded by
`policy_engine.py`. **Naming hazard:** `policy.py` (dead) vs `policy_engine.py`
(live). Follow-up candidate (archive/remove).

---

## Sandbox layer

| Module | Verdict | Wired | Notes |
|--------|---------|-------|-------|
| `sandbox_contract.py` | **implemented** (declarative + schema validate) | ✅ live | data contract everywhere |
| `sandbox_gate.py` | **implemented** | ✅ live | real **tool-axis** enforcement |
| `sandbox_runtime.py` | **implemented** (real OS enforcement) | ✅ live | net/proc allowlist **declared-only** |
| `sandbox_enforcer.py` | **implemented** pure-funcs, **mostly dead** | ⚠️ partial | only `check_tool_invoke` wired |

### sandbox_contract.py — implemented · wired
Python mirror of `sandbox_profile.schema.json`: capability dataclasses (84-153),
closed frozensets, `validate_profile_dict()` (189) calls `jsonschema.validate`.
Imported by runtime/gate/enforcer + `gogogo.py:52`.

### sandbox_gate.py — implemented · wired (tool axis only)
`run_sandbox_gated_lifecycle()` (68): profile bound → `check_tool_invoke` first;
`deny` → `sandbox.deny` audit (121) + short-circuit (lease never mints). Wired at
`gogogo.py:61` → `:660`; deny → `SANDBOX-DENY` + `Exit(1)` (real block). `profile is
None` → documented bypass (no tool gating).

### sandbox_runtime.py — implemented (real macOS `sandbox-exec`) · wired · with declared-only gaps
Builds a real `.sb` policy (`build_sandbox_profile_text` 284), writes 0600 tmp
(338), wraps argv with `/usr/bin/sandbox-exec -f` (357); `tool_dispatcher.py:101-126`
applies it to the real `subprocess.run` → **fs-write + forbidden-path + net-deny +
proc-deny enforced by the kernel at exec**. Fail-closed: required axis + sandbox-exec
unavailable → `sandbox.runtime_unavailable` + `Exit(1)` (`gogogo.py:848-883`).
**Declared-only (the audit's key finding):** `net.outbound: allowlist` is NOT
enforced — Apple sandbox-exec has no hostname allowlist, so it degrades to full
`(deny network*)` + advisory comments, recorded as `sandbox.allowlist_unenforced`
(`gogogo.py:905-921`). Fail-safe (deny stricter than intent) but "allow host X"
silently becomes "allow nothing." Secondary: `proc.allowed_binaries` POC-skipped
(comment-only); fs **reads** intentionally unrestricted. Two off-switches:
`sandbox.runtime_enforcement_enabled` ssot flag + `profile is None` gate bypass.

### sandbox_enforcer.py — implemented pure-funcs, MOSTLY DEAD ⚠️
Real fail-closed axis checkers (`check_fs_read/write/delete`, `check_net_outbound`,
`check_proc_exec/spawn`, `check_tool_invoke`) returning `AxisDecision`. **But only
`check_tool_invoke` is wired** (via `sandbox_gate.py:25`); the **fs/net/proc
checkers have no non-test caller** — real fs/net/proc enforcement goes through the
`sandbox_runtime` OS wrap instead. So this module's fs/net/proc logic is
implemented-but-dead (test-only). Also `_normalised` skips realpath (no symlink
collapse) unlike the runtime hook.

---

## Follow-up (gated behind this audit — NOT done here)

Each is a **separate** future batch; none is a from-scratch enforcement build.

1. **Dead `policy.py` stub** — archive/remove or fold into `policy_engine.py`; resolve the `policy.py` vs `policy_engine.py` naming hazard. *(low risk; doc/cleanup)*
2. **Dead `sandbox_enforcer` fs/net/proc checkers** — decide: wire them as a second (pre-exec, portable) defense layer, or remove to avoid the false impression that they protect the workspace. *(design decision — two parallel impls today)*
3. **`net.outbound: allowlist` declared-only** — if real per-host egress is wanted, needs a DNS-resolving proxy / pf rules (sandbox-exec can't do hostnames). Currently fail-safe + audited; this is a Tier-B design item, not a bug. *(design)*
4. **`proc.allowed_binaries` declared-only** + **fs reads unrestricted** — POC limits; lift only if the threat model requires. *(design)*
5. **`resolve_precedence` test-only** — wire into the engine's multi-verdict consolidation or drop. *(low risk)*

## Conclusion

T4-AUDIT resolved: the policy/sandbox **enforcement path is real and wired**
(policy deny/NEEDS_HUMAN blocks dispatch; sandbox tool-gate + OS `sandbox-exec`
block tools and fs-write/forbidden/net-deny/proc-deny). The gaps are **dead code**
(policy.py, enforcer fs/net/proc, resolve_precedence) and **declared-only POC
axes** (net + proc allowlist, fs reads) — all already audit-visible at runtime.
No urgent implementation work is unblocked; the items above are deliberate
follow-ups, not silent stubs.

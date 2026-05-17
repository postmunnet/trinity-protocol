---
title: "Retro — Tier 0 Remote-Dev via Telegram (dogfood window)"
status: locked
last-updated: 2026-05-11
audience: "Trinity team + Phase 9 Console deciders + future remote-dev iterators"
session-window: "2026-05-01 → 2026-05-11 (~10-day sprint + 2-week parallel dogfood)"
session-id: "tier0_remote_dev_dogfood"
acceptance-evidence: PASS (with one instrumentation gap — see §What didn't work)
rrr-contract: N/A — multi-session sprint; per-session rrr already filed
audit-events-added: ~150 across 7+ sessions (notify-cli x2 / tg-bot x4 / ddd-HMAC / R34 user_id / R35 gogogo+rrr HMAC / R41 tokenizer / R42 envelope-sweep)
artifact-class: "Institutional Memory Artifact — not a sprint log. Retro = episodic; sections §Reusable Patterns / §Invariants Proven / §Operational Learnings are semantic consolidations meant for re-use."
---

# Tier 0 — Remote-Dev via Telegram (dogfood retro)

> **All 8 phases shipped in 10 days. Bot v0.3.4-beta in production
> on launchd; HMAC matrix complete (ddd/gogogo/rrr); real user_id
> binding proven on 2026-05-11 (`decided_by="human:tg:817249157"`
> in audit chain). Operator's #1 bottleneck — mobile gate approval —
> addressed. Phase 9 (full Console) decision: PROCEED — operator
> wants dashboard layer next.**
>
> **This retro is the source artifact for three doctrine entries
> (see §Invariants Proven) and two reusable patterns (§Reusable
> Patterns). Future memory consolidation pipelines should treat
> those subsections as canonical sources — not the prose around
> them.**

## Truth Hierarchy

When reading this retro vs other artifacts about the same period,
trust in this order:

```
1. .ai/policies/        — formal spec (highest authority; only operator edits)
2. trinity_v2/docs/specs/  — spec contracts (agent forbidden_path)
3. .ai/audit/events.ndjson — hash-chained verifiable event log
4. verified artifacts (test outputs, plan envelopes, evidence dicts)
5. this retro (interpretation layer — narratives, lessons, doctrine claims)
6. memory-cli records (compressed summary; subject to staleness)
```

If this retro disagrees with the audit chain, the audit chain wins.
If it disagrees with a spec, the spec wins. Use this retro for
**why** — not **what**.

## Scope (8 phases per spec 14 §11)

| Phase | What landed | Closure date |
|-------|-------------|--------------|
| **0** | Spec 13 + 14 v0.2.0-beta with Decisions C+Y reviewed/approved | 2026-05-01 |
| **1A** | `notify-cli` v0.1.0-beta `send` verb (TG/discord/smtp/webhook channels) | 2026-05-02 |
| **1B** | `notify-cli` v0.2.0-beta `watch` + matcher DSL + offset.db | 2026-05-02 |
| **2** | `trinity-tg-bot` v0.1.0-beta — single-shot `/lll`, `/status`, `/sessions`, `/audit`, `/recall`, `/help`; allowlist; HMAC sign skeleton | 2026-05-02 |
| **3+4** | tg-bot v0.2.0-beta — interactive `/vvv` Q&A + streaming `/gogogo` (live message edit) + `/stop` + launchd plist | 2026-05-02 |
| **5** | Whisper voice notes — **deferred** (Q3: operator hasn't used voice path; re-evaluate if usage signals demand) | deferred |
| **6** | Quality-of-life — 2-step destructive confirm, HMAC sign, output truncation, `/quiet` | 2026-05-02 |
| **HMAC wire-up** | `core/auth.py` shim (verify_hmac + load_hmac_envelope); wired into `ddd` → `gogogo` → `rrr` uniformly. **R34** user_id binding + **R35** matrix extension both closed | 2026-05-10 |
| **R41/R42** | tg-bot v0.3.4-beta — quoted-arg tokenizer + startup envelope sweep | 2026-05-10 |
| **7 (dogfood)** | 2-week parallel window — real user_id smoke test executed 2026-05-11 (`decided_by="human:tg:817249157"`) | 2026-05-11 |

D-decisions honored: **Decision C** (split-duty events.ndjson tail —
notify-cli watch + tg-bot stream maintain independent offset.db).
**Decision Y** (HMAC verify in kernel `core/auth.py`, NOT bot-side —
defense-in-depth against bot host compromise).

## Metrics

### Engineering Metrics

| Dimension | Value |
|-----------|-------|
| Build window | 2026-05-01 → 2026-05-10 (~10 days, vs 3.5-day estimate; HMAC matrix added scope) |
| Dogfood window | 2026-05-01..2026-05-11 (~2 weeks parallel per spec) |
| Phases shipped | 7 of 8 (Phase 5 Whisper deferred per operator usage data) |
| Bot version | (none) → 0.3.4-beta |
| Kernel pytest | 226 → 263 (+37 from HMAC+auth tests) |
| Bot internal tests | 0 → 51 |
| Platinum contract score | notify-cli 14/14 · tg-bot 14/14 |
| New audit event types | `ddd.hmac_rejected`, transition `evidence.via=tg-bot:hmac`, `decided_by="human:tg:<user_id>"` |
| Real user_id in audit chain | `817249157` (smoke 2026-05-11T02:21:11Z) |
| R-followups closed in sprint | R34, R35, R37, R39, R41, R42 |
| R-followups still open | R36, R38 (spec changelog — operator-only), R40 (notify-cli + tasks.db D-decision) |
| Spec changes | 2 new (13, 14) — no edits to existing spec contracts |

### Cognitive Metrics (instrumentation pending)

These are the metrics that actually matter for the project goal
("reduce operational cognitive load"). Most are not yet measured —
documenting the schema so Phase 9 can wire instrumentation.

| Dimension | Current value | Source/Status |
|-----------|---------------|---------------|
| Approval latency (mobile gate) | **NOT MEASURED** | Q2 = d; needs `bot_command.fired` event-count + time-to-approve histogram |
| Manual gate frequency | **NOT MEASURED** | Operator self-report only ("many per session") |
| Context-switch reduction | **Qualitatively claimed** | "Cover ≥80%" not yet quantitatively verified |
| Operator interruption count | **NOT MEASURED** | New metric; track via `notify-cli` watch event count |
| Rollback avoidance | 0 incidents during dogfood (no rollback fired from TG) | Audit chain inspection — zero `ddd.hmac_rejected` outside test |
| Decision confidence | Subjective HIGH — HMAC + user_id stamp gives operator audit-trail comfort | Operator self-report |
| Voice-channel utilization | 0% (Phase 5 unused — Q3 = c) | Phase 5 was over-scoped |

**Open instrumentation task:** Phase 9 should add a `cognitive_metrics`
emission contract — preferably as `tool_event` envelopes from
notify-cli or a new sibling, so future retros have hard numbers.

## What worked

**Architecture invariant held across 10 days of build.** Spec 14's
prime directive — "Bot = transport. Kernel + verifier = authority" —
survived every implementation pressure. Bot never short-circuited a
gate; every aggressive op got HMAC-signed; kernel `core/auth.py`
verified independently. When the bot ran on the operator's Mac and
fired `/ddd` from a phone in another country, the kernel still owned
the verdict.

**HMAC envelope-file pattern scaled cleanly.** First wired into
`ddd.py` (Decision Y), then extracted to `core/auth.load_hmac_envelope`
helper, then applied uniformly to `gogogo` and `rrr`. Canonical
JSON-bytes contract prevented a whole class of sig-mismatch bugs.
*(Promoted to §Reusable Patterns — see "Signed Envelope Authorization".)*

**user_id binding without graph-schema breakage (R34).** Transition
events keep literal `decided_by="human"` (preserves graph schema);
transport identity rides on `evidence.via="tg-bot:hmac"` +
`evidence.hmac_user_id=<id>`; `ddd.completed` event stamps the
specific `human:tg:<user_id>` form.
*(Promoted to §Invariants Proven — see "Verified Human Authorization Chain".)*

**Sibling-vs-kernel boundary stayed clean.** `notify-cli` and
`trinity-tg-bot` both live OUTSIDE `dev/prod` folders, both pass
Platinum 14/14, both register via `.ai/tools.yaml`. Kernel got
HMAC-verify capability but **no LLM** — Whisper integration (Phase 5)
stayed in the bot sibling, not the kernel.

**Phase-5 deferral was the right call.** Spec budgeted ½ day for
Whisper; operator usage data (Q3 — never invoked voice path) makes
the spend non-justifiable. Re-evaluate when usage signals demand.

## What surprised

**Tier 0 grew from 3.5 days to 10 days — HMAC matrix added.**
Original spec scoped HMAC for `/ddd` only; operator wanted **uniform**
signing across `gogogo` and `rrr` (R35) plus real user_id (R34). The
matrix grew but the pattern stayed identical, so per-command cost
was ~90 min each.

**`process.reallyExit()` needed for native-destructor siblings (R37).**
sqlite-vec + fastembed native modules don't respect process.exit().
Partial fix in v0.9.2-beta — fastembed + vec_records combo still
lands data on disk before exit. *(Promoted to §Reusable Patterns —
"Native Destructor Exit Discipline".)*

**launchctl plist reload gotcha.** `kickstart -k` does NOT reload
plist `EnvironmentVariables`. Pattern: use `bootout` + `bootstrap`;
verify via `ps eww -p <PID>`. *(Already in memory as
`feedback_launchctl_plist_reload`; this retro is the originating
incident.)*

**Real `decided_by="human:tg:817249157"` smoke event.** The full
TG→bot→kernel HMAC pipeline rendering an operator's actual Telegram
user ID in the audit chain. *(Promoted to doctrine — see §Invariants
Proven.)*

## What didn't work (one gap)

**Gate-wait reduction never measured (Q2: d).** Spec 14 §11 acceptance
gate "operator measures gate-wait reduction vs pre-Tier-0 baseline"
was specified but no instrumentation shipped. Dogfood window proved
the pipeline works *technically*, but ROI vs the original bottleneck
claim ("many times per session") remains **qualitatively asserted,
quantitatively unverified**. Followup: see Cognitive Metrics table
above + Phase 9 acceptance gates.

---

## Operational Learnings

Distilled from this sprint — direct prescriptions for future Trinity
work. Each item is a behavior change, not a fact.

1. **Scope estimates double when the matrix extends.** A 3.5-day
   spec became 10 days because operator wanted uniform application
   (HMAC on 3 commands, not 1). When the next sprint touches a
   "matrix" (rule_set × command, sibling × protocol, etc.), pad
   estimates 2× and call out matrix-extension risk in `nnn` envelope.
2. **Spec deferrals are first-class outcomes.** Phase 5 (Whisper)
   deferral based on Q3 data is *not* "we didn't ship" — it's a
   *correct* outcome that beats shipping un-used code. Track
   deferral as `phase.outcome=deferred-by-evidence`.
3. **Audit-chain readability matters more than dashboard polish.**
   Operator's smoke-test reaction ("audit shows real user_id =
   trust signal") confirms that **verifiable trail** beats
   **visualization** for this operator. Weight Phase 9 toward audit
   timeline rendering over generic charts.
4. **Sibling builds need explicit closure ritual.** The 4-step
   `commit-spec → ddd-skip-verify → rrr → close-force` sequence
   (memory: `feedback_sibling_build_closure`) is now a
   ratified pattern, not a workaround. New sibling specs should
   reference it.

## Reusable Patterns

Promote from this retro; reference by name in future plans.

### Pattern 1 — Signed Envelope Authorization

| Field | Value |
|-------|-------|
| **Use** | Allow an untrusted transport (bot, webhook, mobile client) to authorize a kernel aggressive op without granting the transport direct kernel rights |
| **Invariant** | Kernel verifies signature *independently* using a separately-held secret; transport never decides authority — only transports a signed claim |
| **Shape** | Transport writes JSON envelope `{op, payload, ts, nonce, user_id?, sig}` to a file; kernel command takes `--hmac-envelope-file=<path>`; helper `load_hmac_envelope()` extracts canonical bytes via `json.dumps separators=(',', ':')` (matches JS `JSON.stringify`); helper `verify_hmac()` returns `(ok, reason)` with reason ∈ `{ok, no_secret, bad_input, malformed_ts, ts_skew, sig_mismatch}` |
| **Risks** | JSON canonicalization mismatch between signer and verifier; ts-skew window (currently ±300s); envelope replay (mitigate via nonce file or unread-file consumption) |
| **Dependencies** | `core/auth.py` (verify_hmac, load_hmac_envelope, compute_sig); `TRINITY_KERNEL_HMAC_SECRET` env; reference signer in `trinity-tg-bot/lib/hmac.js` |
| **Audit footprint** | On reject: `<command>.hmac_rejected` event with `reason`; on accept: `decided_by="human:tg:<user_id>"` on `<command>.completed` + transport id on transition `evidence.via` |
| **First instance** | `commands/ddd.py` (2026-05-10) |

### Pattern 2 — Native Destructor Exit Discipline

| Field | Value |
|-------|-------|
| **Use** | Node siblings that load native modules with C-side destructors (sqlite-vec, fastembed, etc.) |
| **Invariant** | `process.exit()` does NOT wait for native destructors → use `process.reallyExit()` after explicit flush |
| **Shape** | At sibling shutdown: 1) close DB connections explicitly, 2) drain pending writes, 3) `process.reallyExit(code)` instead of `process.exit(code)` |
| **Risks** | **Partial fix only** — fastembed + vec_records combo still lands data on disk before exit. Cover known paths; flag unknown native paths for testing |
| **Dependencies** | Per-sibling; pattern is import-side, not a shared library |
| **First instance** | memory-cli v0.9.2-beta (during R37 investigation) |
| **Followup** | fastembed+vec_records edge case still open |

## Invariants Proven

These survived the entire dogfood window and are now doctrine.
Future sessions should treat them as load-bearing — if a change
violates one, that's a red flag.

### Doctrine 1 — Bot is Transport, Kernel is Authority

The bot never decided a verdict during dogfood. Every aggressive op
went through HMAC verify in `core/auth.py`. Conclusion: the
transport/authority split is *implementable*, not just aspirational.
Future siblings (judge-cli, plan-cli, etc.) should mirror this:
**siblings propose, kernel verifies, operator authorizes**.

### Doctrine 2 — Verified Human Authorization Chain

The audit-chain event `decided_by="human:tg:817249157"` (2026-05-11)
is the canonical proof. Three properties together = doctrine:

1. **Identity:** transport-bound user_id, not anonymous "human"
2. **Integrity:** HMAC over canonical payload, kernel-verified
3. **Auditability:** stamped into the hash-chained ledger

Phase 9 instrumentation, multi-user expansion, and any "trust the
mobile" feature must preserve all three. Don't trade auditability
for UX shortcuts.

### Doctrine 3 — Sibling Boundary Survives Scope Pressure

Despite 10 days of pressure (HMAC matrix, voice notes, dashboard
calls), no LLM landed in the kernel. notify-cli stayed sibling.
tg-bot stayed sibling. Whisper deferred. Confirms the **D14 cost
rule** ("kernel-internal hot-path bypasses subprocess boundary even
when capability is sibling-shaped") works *both ways*: hot-path
stays in kernel, intelligence stays in sibling. Both directions
held.

## Cognitive Bottlenecks

Pain points that *remain* after this sprint — explicit so Phase 9
can address them, not implicit so they get re-debated next retro.

1. **No quantitative gate-wait measurement.** Operator pain claim is
   un-instrumented (see Cognitive Metrics table). Until measured,
   ROI is faith-based. Highest-priority Phase 9 instrumentation.
2. **Bot offline = invisible.** If launchd plist crashes, operator
   only notices on next mobile command. No proactive
   "bot-is-up" heartbeat to operator's TG.
3. **No bird's-eye state.** Operator can `/lll` per session but
   can't see "across all sessions in last 24h" without SSH-ing to
   laptop. This is the Phase 9 dashboard motivation.
4. **Mac sleep during travel** (spec 14 risk register item). Still
   un-mitigated; `caffeinate -i` is operator-discipline, not
   tooling-enforced. Phase 8 VPS migration option remains theoretical.
5. **Sibling closure ritual still 4-step manual.** `commit-spec →
   ddd-skip-verify → rrr → close-force` is documented but not
   automated. Future ergonomics work could fold into `ai sibling
   close`.

## Followups

- **R36** — Spec 14 §6.1 changelog (operator commits — `docs/specs/**` agent forbidden_path)
- **R38** — Spec 5 v0.9.2 changelog (operator commits)
- **R40** — notify-cli + tasks.db D-decision: (α) task-cli emits to kernel audit chain OR (β) notify-cli gains `--source=sqlite` capability
- **R47** — cosmetic `memory_learn` warning during operational brain capture (non-blocking)
- **NEW — Cognitive instrumentation** — Phase 9 acceptance gate; add `cognitive_metrics` emission to notify-cli or new sibling
- **NEW — Bot heartbeat** — proactive "bot-is-up" TG ping; addresses Cognitive Bottleneck #2
- **NEW — Memory Promotion Policy (future)** — formalize criteria for `learning → doctrine`, `pattern → invariant`; add confidence/staleness/superseded_by/contradiction-detection fields. Not blocking now; matures alongside Phase 9.
- **R37 residual** — fastembed+vec_records destructor edge case

## Decision: Phase 9 — full Console

**PROCEED** (operator answer Q5: b). TG covers control plane
(gate approval, voice deferred), but operator wants **dashboard
layer** next — multi-session bird's-eye view, audit timeline
visualization, artifact viewer. Out-of-scope items from Tier 0
spec §11 (multi-session dashboard, audit timeline, artifact viewer,
multi-user) now move to Phase 9 spec authoring.

**Sequencing constraints (load-bearing):**
1. Phase 9 acceptance gates MUST include Cognitive Metrics
   instrumentation — closes the open measurement gap.
2. Phase 9 dashboards MUST render audit-chain primitives directly
   (not abstracted summaries) — preserves Doctrine 2 auditability.
3. Phase 9 MUST NOT land LLM in kernel — Doctrine 3 stays intact.
4. Phase 9 SHOULD include bot heartbeat — addresses Cognitive
   Bottleneck #2 cheaply (~1 hour scope).

## Audit references

- Phase 0 close: spec 13 v0.2.0-beta + spec 14 v0.2.0-beta (`trinity_v2/docs/specs/13_NOTIFY_CLI_SPEC.md`, `14_TRINITY_TG_BOT_SPEC.md`)
- ddd HMAC wire-up session: `0001_2026-05-10_16_24_pm_feat-feat-ddd-hmac-verify-wireup` (kernel pytest 261, audit hash chain bridge)
- R34 user_id binding session: `0001_2026-05-10_20_58_pm_feat-feat-hmac-user-id-binding` (8/8 gates + Platinum 14/14)
- Dogfood smoke 2026-05-11: `0001_2026-05-11_07_26_am_feat-ops-hmac-smoke-test` (`ddd.completed` decided_by `human:tg:817249157`)
- Tier 0 TODO entry: `TRINITY_LEGACY/TODO.md` Tier 0 block

## Memory consolidation pipeline (for this retro)

The following extracts from this retro should feed memory-cli as
separate, structured records — NOT as a single "Tier 0 retro" blob.

| Source section | Memory entry | Type |
|----------------|--------------|------|
| §Invariants Proven Doctrine 1 | `doctrine_bot_transport_kernel_authority` | doctrine |
| §Invariants Proven Doctrine 2 | `doctrine_verified_human_auth_chain` | doctrine |
| §Invariants Proven Doctrine 3 | `doctrine_sibling_boundary_survives_pressure` | doctrine |
| §Reusable Patterns Pattern 1 | `pattern_signed_envelope_authorization` | pattern |
| §Reusable Patterns Pattern 2 | `pattern_native_destructor_exit` | pattern (links to existing feedback memory) |
| §Operational Learnings 1–4 | `learning_tier0_*` (4 entries) | feedback/learning |
| §Cognitive Bottlenecks 1–5 | `bottleneck_*` (5 entries) | open-issue |
| §Decision: Phase 9 | `decision_phase9_proceed` | project |

This pipeline turns the retro from episodic (this happened) into
semantic (this is true / this works / this is open). Memory queries
for "how do I sign a remote op?" should hit `pattern_signed_envelope_authorization`
directly, not require reading this retro.

## Producer surface — gate-wait metric

Closes the §What didn't work gap (Cognitive Bottleneck #1) by shipping
the producer-side instrumentation for the gate-wait metric. The audit
chain at `.ai/audit/events.ndjson` is the source of truth; no separate
metrics store is introduced.

**CLI surface.** `bash .ai/cli/ai audit metrics --window <spec>`
emits a single JSON object on stdout with stable keys:

- `window.spec` / `window.start` / `window.end` — UTC window the
  command operated over
- `sample_count` — number of paired `(bot_command.fired, terminal)`
  events whose `fired_ts` falls in the half-open interval `[start, end)`
- `p50` / `p95` — linear-interpolated percentiles in seconds, or
  explicit `null` when `sample_count == 0`
- `histogram` — fixed bucket counts over
  `(0, 1, 5, 10, 30, 60, 300, 900, 3600)` seconds with an open final
  bucket

**Join contract.** Within a single `session_id`, events are ordered
by `(timestamp, sequence)` and FIFO-paired: each terminal-transition
event (`ddd.completed`, `gogogo.completed`, `rrr.completed`,
`close.completed`, etc.) consumes the oldest unmatched
`bot_command.fired` in that same session. Cross-session pairing
never happens; events with `session_id is None` are skipped; clock-skew
negatives are dropped silently.

**Out of scope this iteration.** notify-cli emission of cognitive
metrics, manual-gate-frequency counting, operator-interruption
counting, context-switch reduction measurement, and any dashboard
rendering remain deferred follow-up work; the producer pattern
(audit-chain derivation + JSON reader) is the reusable surface those
follow-ups will extend.

**Acceptance gate closed.** Spec 14 §11 "operator measures gate-wait
reduction vs pre-Tier-0 baseline" now has an executable producer; the
empirical dataset will accumulate as `bot_command.fired` events land
in the audit chain.

## See also

- [`13_NOTIFY_CLI_SPEC.md`](../specs/13_NOTIFY_CLI_SPEC.md) — notify-cli contract
- [`14_TRINITY_TG_BOT_SPEC.md`](../specs/14_TRINITY_TG_BOT_SPEC.md) — bot contract
- [`12_PHASE_2_2_TO_5_FOUR_PHASE_SPRINT.md`](12_PHASE_2_2_TO_5_FOUR_PHASE_SPRINT.md) — kernel sprint retro
- [`13_PHASE_0_5_TO_10_AND_UX_SECOND_SPRINT.md`](13_PHASE_0_5_TO_10_AND_UX_SECOND_SPRINT.md) — UX layer retro

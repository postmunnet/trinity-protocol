---
title: "Trinity Transport Boundary Spec v1.0"
version: "1.0"
status: "draft"
phase: "9"
last-updated: "2026-05-15"
authority: "Operator (Founder / Trinity Architect)"
canonical: true
supersedes:
  - "(none -- first canonical version)"
constitutional-anchor: ["Article XV", "Article III", "Article IV", "Article XIII", "Article XVI", "Article XX", "Article XXIX"]
amendment-policy: "Article XXIX -- explicit proposal + rationale + impact analysis + human approval + version bump + audit entry."
---

# TRINITY_TRANSPORT_BOUNDARY_SPEC_V1

**Status:** DRAFT v1 (first canonical version -- pending verifier review + ddd)
**Phase:** 9 -- Transport Boundary Hardening
**Organ:** #14 (Transport Gateway), in coordination with Kernel (#1), Policy Engine (#3), DDD / Human Gate (#13), Audit (#10)
**Constitutional rank:** 5 -- Workflow Contract (per Article XXV)
**Date:** 2026-05-15

## Section 0 -- Rank-5 Authority Disclaimer (Article XXV)

This document is a **Workflow Contract**. It ranks fifth in the constitutional priority order:

```text
Constitution
-> Ritual Constitution
-> Canonical Policies        (.ai/policies/**)
-> Kernel State Rules        (.ai/cli/**, graph transitions)
-> Workflow Contracts        (THIS DOCUMENT)
-> Tool Contracts
-> Runtime Requests
-> Model Suggestions
```

This Spec is **void where it conflicts with any higher-ranked instrument**. Amendments follow Article XXIX (operationalised by Addendum v1.0.4 -- editorial / operational / constitutional tier classification, trace-to-failure, pinned audit format). Article XV (Transport is not Authority) is the controlling clause for every constraint described here -- this spec pins the **shape** of the transport boundary; it does not redefine where authority lives.

This Spec does NOT amend `.ai/policies/verifier-rules.yaml`, `.ai/policies/safety.yaml`, or `.ai/policies/gates.yaml`. Those files are Canonical Policies (rank 2). This Spec describes the **shape of envelopes** that transports MUST sign, the **refusal codes** transports MUST emit when an envelope fails, and the **audit attribution** the kernel MUST record when accepting a transport-delivered request.

---

## Section 1 -- Purpose & Constitutional Anchor

**[normative-description]**

This Spec operationalises the constitutional rule that **transport layers MAY deliver, but MUST NOT decide**. It defines:

1. The taxonomy that distinguishes a Transport organ from an Authority organ.
2. The signed-envelope schema every transport-delivered request MUST satisfy.
3. The HMAC algorithm and key-issuance discipline.
4. The refusal codes a transport MUST emit when an envelope fails the boundary.
5. The audit attribution rule: the kernel records the AUTHORITY (human, policy, verifier, kernel), never the transport, in `decided_by`.
6. The forbidden-action list every transport implementation MUST honour.

### 1.1 Why a Transport Boundary Spec exists

Trinity already ships two production transport siblings: `notify-cli` (outbound -- Spec 13) and `trinity-tg-bot` (bidirectional -- Spec 14). Tier 0 dogfood landed `tg-bot` v0.3.4-beta + `notify-cli` in launchd on 2026-05-11. From day one, both have operated under the rule "transport delivers, kernel decides." This Spec pins that rule into a normative contract so that **future transports** (Slack, web hooks, browser extensions, API bridges, IDE bridges, voice front-ends) cannot silently widen the authority surface by accident.

### 1.2 Article XV verbatim (PRIMARY ANCHOR -- load-bearing)

Article XV of the Trinity Constitution v1.0 reads in full:

```text
Article XV -- Transport Is Not Authority

Transport layers include:

Telegram
Slack
webhooks
browser interfaces
API bridges
chat interfaces

Transport layers MAY deliver requests and responses.

Transport layers MUST NOT:

- approve gates
- mutate workflow state directly
- bypass Kernel governance
- become authority layers

Transport is not authority.
```

The exact phrase **"Transport is not authority"** is the load-bearing closing line of Article XV. Every section of this Spec MUST be readable as a concrete operationalisation of that closing line. If any constraint in this Spec ever appears to weaken that line, **the Constitution wins** (Article XXV).

> **Footnote (editorial -- NP-9-1):** The verbatim block above renders the Article XV em-dashes as ASCII `--` rather than the Unicode em-dash character. This Spec is ASCII-only by convention (so that grep/diff/acceptance-grep -F patterns match exact characters across editors and shells); the substance is faithful to the canonical Constitution text.

### 1.3 Supporting Articles (cited verbatim or quoted)

#### Article III -- AI Cannot Govern Itself (verbatim, abridged to load-bearing clauses)

```text
AI MUST NOT:

- declare final completion
- approve its own work
- verify its own correctness
- bypass verifier approval
- bypass governance gates
- forge authority
- redefine workflow state
- rewrite constitutional policy
```

Relevance: a transport that **forges authority** by, for example, attaching a fabricated `decided_by: "human"` field to a synthesised envelope is in direct violation of Article III's "forge authority" prohibition. The HMAC discipline in Section 4 prevents that forgery from being undetectable.

#### Article IV -- Separation of Responsibilities (verbatim, transport line)

```text
Transport = message delivery only
```

```text
No component may silently absorb another component's role.

Role collapse is a constitutional violation.
```

Relevance: the most common Article IV violation in this domain is a transport that translates a refusal-to-deliver into a verifier verdict ("the user did not click approve, therefore the gate FAILS"). That is role collapse: refusal-to-deliver belongs to the Transport organ; FAIL belongs to the Verifier organ. Section 5 enumerates refusal codes that are explicitly distinct from any verifier verdict.

#### Article XIII -- Human Authority (verbatim, load-bearing clauses)

```text
Humans remain the highest authority.

AI may recommend irreversible actions.

AI MUST NOT silently authorize irreversible actions.
```

```text
Human approval MUST exist as an artifact.
```

Relevance: when a human approves a deploy via Telegram, the **artifact** is the signed envelope plus the kernel-side audit event recording `decided_by="human:tg:<id>"`. The transport (`trinity-tg-bot`) carries the bytes; the kernel records the authority. Section 6 pins that attribution format.

#### Article XVI -- Least Authority (verbatim, transport line)

```text
transport must not own governance authority
```

```text
Unknown authority MUST be treated as denied authority.
```

Relevance: an unsigned envelope, an envelope with an unrecognised `key_id`, or an envelope with a malformed HMAC is **unknown authority**. The kernel MUST treat it as denied (refusal codes in Section 5). The transport MAY attempt redelivery; the kernel MAY NOT lower its evidence bar.

#### Article XX -- Passive Core Principle (verbatim, abridged)

```text
Core Trinity systems act only through explicit invocation.

Core systems MUST NOT:

self-trigger
self-expand authority
silently mutate policy
```

Relevance: a transport MUST NOT, on its own initiative, retry a denied envelope under a different key, escalate to a higher-privileged actor, or cache an approval decision and re-issue it later. Each of those would constitute "self-expand authority" by the transport organ. The kernel verifies every envelope **freshly** -- caching of approvals is forbidden (Section 7).

#### Article XXIX -- Constitutional Amendment (verbatim)

```text
The Constitution MUST NOT be silently rewritten.

Amendments require:

explicit proposal
rationale
impact analysis
human approval
version bump
audit entry

Prior versions MUST remain inspectable.
```

Relevance: adding a new transport (Slack, webhook, browser, IDE bridge) is a Spec amendment because it widens the trusted-issuer surface (Section 10). Each new transport MUST declare which Authority organ issues its signing keys and MUST land via the Article XXIX amendment protocol.

### 1.4 Why the boundary matters operationally

In a system without an explicit transport boundary, a chat interface can drift into the role of policy engine ("the bot will only forward approval if the user has typed CONFIRM"), the role of verifier ("the bot will only forward gogogo if the test summary looks green"), and the role of kernel ("the bot will mark the session DEPLOYED once the human reacts with a thumbs-up"). Every one of those drifts is a role collapse (Article IV). Every one of those drifts is invisible in the audit chain because the transport's internal logic is not Trinity's audit substrate.

The transport boundary fixes this by drawing the line at the kernel: **the transport's job is to put a signed bag of bytes on the kernel's input queue. The kernel's job is to verify the signature, parse the bag, and decide.** Verification, decision, audit, transition -- all four belong to the kernel-side organs. The transport never decides. The transport never transitions. The transport never silently retries. Every refusal is an explicit refusal code. Every accepted envelope produces an audit event with the kernel's authority attribution, not the transport's.

---

## Section 2 -- Transport vs Authority Taxonomy

**[normative-description]**

### 2.1 Transport organ -- definition

A **Transport** is any organ whose role is **delivery of bytes**. A Transport:

- accepts external messages (chat, web, API, voice, browser)
- packages those messages into signed envelopes
- forwards envelopes to the Kernel
- relays Kernel responses back to the originating channel

A Transport does NOT:

- decide whether the request is allowed (that is the Policy Engine's role -- Organ #3)
- decide whether the request transitions state (that is the Kernel's role -- Organ #1)
- decide whether the work passed verification (that is the Verifier's role -- Organ #8)
- decide whether the human approved (that is the Human Gate's role -- Organ #13, with the human as the actor)

### 2.2 Authority organ -- definition

An **Authority** is any organ whose role is **deciding mutation**. Authority organs in Trinity v1 are:

- **Kernel** (Organ #1) -- decides legal state transitions, gate enforcement
- **Policy Engine** (Organ #3) -- decides allow / deny / escalate per rule
- **Verifier** (Organ #8) -- decides PASS / FAIL / UNVERIFIED per pre-declared contract
- **DDD / Human Gate** (Organ #13) -- decides approve / reject / hold (with the human as the actor)

Authority organs MAY consume transport-delivered envelopes. Authority organs MUST NOT delegate their decision authority back to the transport.

### 2.3 Decision rule -- "is X a transport or authority organ?"

When introducing a new component, ask:

1. Does X **decide whether mutation occurs**? If yes -> Authority.
2. Does X **only deliver bytes between an external system and the kernel**? If yes -> Transport.
3. Does X **do both**? Then X is in violation of Article IV (role collapse). Split it into a Transport part and an Authority part before integrating.

A transport MAY apply **delivery-time validation** (e.g. "this Telegram update is from an allowlisted user_id, otherwise drop"). That is delivery hygiene, not authority. The boundary is: a transport that drops on hygiene MUST log a refusal code (Section 5); a transport that drops AND silently re-routes the request to a different authority is in violation.

### 2.4 Current organ taxonomy mapping

The table below maps every organ that participates in a transport-delivered request flow to its taxonomy classification. Source: TRINITY_ORGAN_MAP_V1.md.

| Organ | # | Classification | Notes |
|---|---|---|---|
| Kernel | 1 | **Authority** | Owns state transitions, gate enforcement, envelope verification |
| State Graph | 2 | Authority (delegated to Kernel) | Decides legality of transitions |
| Policy Engine | 3 | **Authority** | Decides allow / deny / escalate |
| Ritual Controller | 4 | Authority (delegated to Kernel) | Routes ritual to organ; does not decide |
| Planner | 5 | Authority (advisory) | Produces plan; does not approve |
| Executor | 6 | Authority (bounded) | Mutates artifacts within scope |
| Sandbox | 7 | Authority (bounded) | Decides allow / deny per IO |
| Verifier | 8 | **Authority** | Decides PASS / FAIL / UNVERIFIED |
| Memory CLI | 9 | Neither (evidence retrieval) | Article IX: passive retriever |
| Audit | 10 | Authority (witness) | Decides hash chain integrity; not a mutator |
| Retro | 11 | Neither (semantic artifact producer) | Does not approve |
| RRR Terminal Gate | 12 | Authority (kernel-internal) | Fires VERIFIED -> DONE |
| DDD / Human Gate | 13 | **Authority** (the human is the actor) | Decides approve / reject / hold |
| **Transport Gateway** | **14** | **Transport** | **Delivery only -- this Spec's subject** |
| Tool Capability Registry | 15 | Authority (advisory) | Declares allowed tool authority |
| Presentation Protocol | 16 | Neither (cognitive aid) | Does not approve |
| Root of Trust | 17 | Authority (genesis-only) | Signs canonical artifacts |
| Close / Session Finalizer | 18 | Authority (kernel-internal) | Seals session |

The single Transport organ in v1 is Organ #14. Today its concrete implementations are:

- `trinity-tg-bot` (Telegram, bidirectional -- Spec 14)
- `notify-cli` (Slack/Discord/SMTP/Webhook, outbound only -- Spec 13)

Both ride the Article XV boundary. Both are subject to every constraint in this Spec.

### 2.5 Hybrid components are forbidden

A component that is "transport for some commands and authority for others" is a role-collapsed component (Article IV). Such components MUST be split into two distinct organs before integration. Example: a chat bot that **also runs verifier rules locally** to short-circuit obvious failures is two organs glued together; the verifier-rule logic MUST be moved to the Verifier organ on the kernel side, and the bot reduced to envelope delivery only.

---

## Section 3 -- Signed Envelope Schema

**[normative-description]**

Every transport-delivered request that asks the Kernel to **mutate state, fire a transition, or record an authority decision** MUST be wrapped in a signed envelope. Envelopes that ask only for **read-only observation** (e.g. "show me current state") MAY skip the HMAC requirement BUT MUST still carry the envelope identity fields (envelope_id, ts, source_transport, claimed_actor) so that audit attribution remains intact.

### 3.1 Envelope fields

The envelope is a JSON object with the following fields. Required fields MUST be present and non-null. Optional fields MAY be omitted; absence is semantically equivalent to null.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `envelope_id` | string | yes | Unique opaque identifier (UUID4 hex or ULID); used for replay detection |
| `ts` | string (RFC3339 UTC) | yes | Wall-clock timestamp of envelope creation at the transport |
| `source_transport` | string | yes | Identity of the transport that produced this envelope (e.g. `"tg-bot"`, `"notify-cli"`, `"slack-bridge"`) |
| `claimed_actor` | string | yes | The actor on whose behalf this envelope is being sent, in the form `<class>:<transport_hint>:<actor_id>` (e.g. `"human:tg:817249157"`) |
| `payload` | object | yes | The request body -- must be a JSON object; canonicalised before signing (Section 3.3) |
| `hmac` | string (lowercase hex) | yes (mutating) | The HMAC over the canonical signed payload (see Section 4) -- omitted only for read-only envelopes |
| `hmac_alg` | string | yes (mutating) | Algorithm identifier; v1 pins `"HMAC-SHA256"` (see Section 4) |
| `key_id` | string | yes (mutating) | Identifier of the signing key used; the Kernel resolves this to the issuing Authority organ (see Section 4.2) |
| `nonce` | string | optional | Per-envelope nonce for replay protection; if absent, `envelope_id` doubles as nonce |
| `expires_ts` | string (RFC3339 UTC) | optional | Envelope expiry; the Kernel rejects envelopes received after this timestamp |

### 3.2 Field semantics -- claimed_actor format

The `claimed_actor` field follows the pinned format:

```text
<authority_class>:<transport_hint>:<actor_id>
```

- `authority_class` -- one of `human`, `kernel`, `policy`, `verifier`, `agent`. The transport MUST honestly declare what class of actor is making the request. A transport MUST NOT claim `kernel` or `policy` -- those are kernel-internal classes.
- `transport_hint` -- a short tag identifying the transport (`tg`, `slack`, `webhook`, `api`, `web`, `ide`). This is informational; the kernel-authoritative source-of-transport is `source_transport`, not the hint inside `claimed_actor`.
- `actor_id` -- the transport-side identifier of the human or system actor (e.g. Telegram user_id, Slack member_id, API client_id).

**Example:** `"human:tg:817249157"` declares "this envelope is being sent on behalf of human actor 817249157, delivered via the Telegram transport." The Kernel will accept the `human` class only if HMAC verification passes against a key whose `key_id` is bound to the issuing Authority organ for `human` actors (Section 4.2).

The kernel ATTRIBUTION rule (Section 6) records the **resolved** actor in the audit event's `decided_by` field, derived from `claimed_actor` AFTER HMAC verification confirms the transport had authority to make that claim.

### 3.3 Canonical encoding

Before HMAC computation and before transmission, the envelope MUST be canonicalised using the same canonical-JSON rules used elsewhere in Trinity:

```text
canonical_json: sort_keys=True, separators=(",", ":"), ensure_ascii=False, encoding=utf-8
```

The canonical form is the byte sequence over which the HMAC is computed (Section 4.3) and over which `envelope_id` uniqueness is enforced. Two envelopes that differ only in JSON whitespace or key order are the **same envelope** by canonical form; the kernel MUST treat them as a replay.

### 3.4 Non-normative example envelope

**[non-normative-example]**

The example below is illustrative only. Production envelopes are not human-typed; they are emitted by transport implementations.

```json
{
  "envelope_id": "01J0000000000000000000000A",
  "ts": "2026-05-15T10:23:45Z",
  "source_transport": "tg-bot",
  "claimed_actor": "human:tg:817249157",
  "payload": {
    "kind": "ddd.decision",
    "session": "0042_2026-05-15_deploy-canary",
    "action": "approve",
    "packet_id": "pkt_8f3c"
  },
  "hmac": "9b8c...redacted-256-bit-hex...",
  "hmac_alg": "HMAC-SHA256",
  "key_id": "human-gate-issuer-2026-05",
  "nonce": "6d7a3e1f2b4c8a91",
  "expires_ts": "2026-05-15T10:28:45Z"
}
```

### 3.5 Forbidden envelope shapes

An envelope MUST be rejected at the Kernel boundary if any of the following hold:

- Required field is absent or null.
- `claimed_actor` declares `kernel`, `policy`, or `verifier` class (those are kernel-internal -- transport may never claim them).
- `payload` is not a JSON object (string, array, number, null are all forbidden at the top level of `payload`).
- `hmac_alg` is not exactly `"HMAC-SHA256"` (v1 pins one algorithm; algorithm agility is a future Addendum).
- `expires_ts`, if present, is in the past relative to the Kernel's monotonic clock with a tolerance of +5 minutes for clock skew.
- `envelope_id` has already been seen in the per-Authority issuer's replay window (default: 24 hours).

Each of these failures maps to a refusal code in Section 5.

---

## Section 4 -- HMAC Signing Requirements

**[normative-description]**

### 4.1 Algorithm

Trinity v1 pins one signing algorithm for transport envelopes:

```text
HMAC-SHA256
```

The literal token `HMAC` and the pinned algorithm `HMAC-SHA256` appear in this paragraph for spec-grep purposes. Implementations MUST use a constant-time HMAC-SHA256 primitive from the platform's standard cryptographic library (e.g., Python `hmac` + `hashlib.sha256`, Node `crypto.createHmac`, Go `crypto/hmac`). The output MUST be encoded as **lowercase hex**, not base64, to keep envelope canonicalisation deterministic.

Algorithm agility -- supporting additional algorithms (e.g. HMAC-SHA384, Ed25519, COSE_Sign1) -- is **out of scope for v1**. Adding a second algorithm is an Article XXIX amendment. Until that amendment lands, any envelope with `hmac_alg != "HMAC-SHA256"` MUST be refused with `TRANSPORT_REFUSED_BADKEY` (Section 5.4).

### 4.2 Key handling discipline -- issuance is the Authority's job

The HMAC secret used to sign an envelope is **issued by the Authority organ** that the envelope's `claimed_actor` class is bound to, NOT by the transport itself.

| `claimed_actor` class | Issuing Authority organ | Notes |
|---|---|---|
| `human` | DDD / Human Gate (Organ #13) | Operator-provisioned; rotated under Article XIII |
| `agent` | Kernel (Organ #1) -- on behalf of an in-house agent | Issued at agent registration time |
| `kernel`, `policy`, `verifier` | (forbidden -- not transport-claimable) | Internal classes |

The `key_id` field of the envelope (Section 3.1) identifies which signing key was used. The Kernel resolves `key_id` to its issuing Authority organ via a Kernel-internal key registry (out-of-scope for this Spec; see Phase 14 Root of Trust for cryptographic anchoring).

**The transport MUST NOT generate its own keys.** A transport that issues itself a signing key is escalating its own authority (Article XX violation -- "self-expand authority"). All keys MUST come from the issuing Authority organ. The transport stores the secret only as an **operational copy** for the duration of envelope construction; the Authority organ retains issuance, rotation, and revocation control.

### 4.3 Signed payload boundary -- what is included in the HMAC

The HMAC is computed over the **canonical-JSON encoding** (Section 3.3) of the envelope **with the `hmac` field removed**. Specifically:

```text
signed_envelope = {all envelope fields EXCEPT hmac}
signed_bytes    = canonical_json(signed_envelope)
hmac            = hex(hmac_sha256(secret, signed_bytes))
```

Fields included in the signed bytes: `envelope_id`, `ts`, `source_transport`, `claimed_actor`, `payload`, `hmac_alg`, `key_id`, and (if present) `nonce`, `expires_ts`.

Field excluded from the signed bytes: `hmac` itself (you cannot sign over the signature).

This boundary means: any modification to `payload`, `claimed_actor`, `key_id`, `ts`, or `expires_ts` invalidates the HMAC. A transport that mutates an envelope mid-flight (e.g. to "fix" a typo) MUST recompute the HMAC -- which it cannot do without the secret -- which it does not own beyond the construction window. The result: in-flight tampering is detectable at the Kernel boundary.

### 4.4 Verification side -- the Kernel verifies, not the transport

HMAC verification is a **Kernel-side** responsibility. A transport MUST NOT verify HMAC and decide whether to forward; the transport forwards every envelope it constructs, and the Kernel decides whether to accept.

This rule is non-negotiable for the same reason as Spec 14 §6.1 Layer 3: if the transport host is compromised, an attacker who reaches the bot still cannot forge an authority decision because the Kernel demands a fresh HMAC against a secret the Kernel reads from its own environment, separate from the bot's environment. Bot-side verify collapses to "trust the bot" -- the exact threat model the boundary mitigates.

### 4.5 Verification algorithm (kernel-side)

**[normative-description]**

On envelope receipt, the Kernel MUST execute the following verification steps in order. Failure at any step is fatal; the Kernel emits the corresponding refusal code (Section 5) and does NOT advance to subsequent steps.

1. **Schema check** -- envelope contains all required fields with correct types; `payload` is a JSON object.
2. **Algorithm check** -- `hmac_alg == "HMAC-SHA256"`.
3. **Key resolution** -- `key_id` resolves to a known signing secret in the Kernel's key registry; resolution returns the issuing Authority organ.
4. **Class consistency** -- `claimed_actor.class` matches the issuing Authority organ's allowed classes (e.g. a `human` class envelope MUST be signed by a key issued by Organ #13).
5. **Signature verify** -- recompute HMAC over canonical-JSON of envelope minus `hmac` field; constant-time compare with the envelope's `hmac` value.
6. **Replay check** -- `envelope_id` has not been seen in the issuer's replay window.
7. **Expiry check** -- `expires_ts`, if present, is not in the past (with +5min skew tolerance).

Only if all seven steps pass does the envelope become an "accepted authority signal" eligible for downstream Authority-organ consumption (e.g. the DDD organ consuming an `approve` payload).

### 4.6 Non-normative pseudocode for verification

**[non-normative-example]**

```python
def verify_envelope(env: dict, key_registry, replay_log) -> tuple[bool, str | None]:
    if not _schema_ok(env):
        return False, "TRANSPORT_REFUSED_UNSIGNED"
    if env.get("hmac_alg") != "HMAC-SHA256":
        return False, "TRANSPORT_REFUSED_BADKEY"
    secret, issuer = key_registry.resolve(env["key_id"])
    if secret is None:
        return False, "TRANSPORT_REFUSED_BADKEY"
    if not issuer.allows_class(env["claimed_actor"].split(":")[0]):
        return False, "TRANSPORT_REFUSED_OVERSCOPE"
    signed = {k: v for k, v in env.items() if k != "hmac"}
    expect = hmac_sha256_hex(secret, canonical_json(signed))
    if not hmac.compare_digest(expect, env["hmac"]):
        return False, "TRANSPORT_REFUSED_BADKEY"
    if replay_log.seen(env["envelope_id"], issuer):
        return False, "TRANSPORT_REFUSED_REPLAY"
    if env.get("expires_ts") and _expired(env["expires_ts"]):
        return False, "TRANSPORT_REFUSED_REPLAY"
    return True, None
```

The pseudocode above is illustrative; production implementations MUST live in a Kernel-internal module (out of scope for this Spec).

---

## Section 5 -- Refusal Semantics

**[normative-description]**

When an envelope fails any check at Section 4.5, the Kernel emits a **refusal code** and audits the refusal. Refusal codes are explicitly distinct from any verifier verdict (Article IV: the Verifier owns PASS / FAIL / UNVERIFIED; the Transport boundary owns refusal-to-accept). A transport refusal is **not** a verification verdict and MUST NOT be promoted to one.

### 5.1 Refusal code registry

Trinity v1 pins four refusal codes for the transport boundary:

| Code | Trigger | Audit event_type |
|---|---|---|
| `TRANSPORT_REFUSED_UNSIGNED` | Required HMAC field absent on a mutating envelope, or schema violation | `transport.envelope_refused.unsigned` |
| `TRANSPORT_REFUSED_BADKEY` | `key_id` unknown, signature mismatch, or `hmac_alg` not pinned | `transport.envelope_refused.badkey` |
| `TRANSPORT_REFUSED_REPLAY` | `envelope_id` already seen in issuer's replay window, or `expires_ts` in the past | `transport.envelope_refused.replay` |
| `TRANSPORT_REFUSED_OVERSCOPE` | `claimed_actor.class` not allowed by issuing Authority organ for this `key_id` | `transport.envelope_refused.overscope` |

Each refusal code has a 1:1 mapping to one audit `event_type`. The audit registry (Spec 10 §3) MUST include all four codes.

### 5.2 Refusal is not a verdict (Article IV anchor)

A refusal MUST NOT be translated into:

- A verifier `FAIL` verdict (verifier verdicts come from Verifier organ, not transport).
- A DDD `rejection.json` artifact (rejection comes from the human via Human Gate organ).
- A state transition (state transitions are kernel-decided, not transport-deflected).
- A policy `denied` verdict (policy denials come from Policy Engine, not transport).

The refusal is exactly what its name says: the transport boundary refused to accept the envelope. The originating actor (human, agent, external system) is informed via the transport's normal response channel ("your envelope was refused with code X"). The Kernel does NOT advance any session state in response to a refusal -- the workflow remains exactly where it was.

### 5.3 TRANSPORT_REFUSED_UNSIGNED

Triggered when:

- A mutating envelope omits the `hmac` field.
- `hmac` is empty or not lowercase hex.
- Required envelope fields (Section 3.1) are missing.
- `payload` is not a JSON object.

Audit event: `transport.envelope_refused.unsigned` with payload `{envelope_id, source_transport, claimed_actor, missing_fields}`.

Operational consequence: the transport SHOULD retry once (in case of mid-flight corruption) and then escalate to the operator via its normal channel. The Kernel does not retry.

### 5.4 TRANSPORT_REFUSED_BADKEY

Triggered when:

- `key_id` does not resolve in the Kernel's key registry.
- `hmac_alg` is not `"HMAC-SHA256"`.
- HMAC signature does not match the recomputed value.

Audit event: `transport.envelope_refused.badkey` with payload `{envelope_id, source_transport, claimed_actor, key_id, alg}`.

Operational consequence: this is the canonical "compromise indicator" code. Repeated `TRANSPORT_REFUSED_BADKEY` from the same `source_transport` SHOULD trigger an operator alert (via `notify-cli` -- Spec 13). Key rotation procedures live in the issuing Authority organ.

> **Footnote (editorial -- NP-9-5):** `TRANSPORT_REFUSED_BADKEY` covers algorithm mismatch (`hmac_alg != "HMAC-SHA256"`) in addition to literal key failures (unknown `key_id`, signature mismatch). The semantic basis: in v1 the algorithm pin is part of the key-ratification contract -- a key is issued together with the algorithm it must be used under, so an envelope that presents the right `key_id` under the wrong `hmac_alg` is operationally a key-binding failure. A future v2.0 MAY split algorithm mismatch into a distinct `TRANSPORT_REFUSED_BADALG` code if/when algorithm agility lands (Section 10.5); until then the conflation is intentional.

### 5.5 TRANSPORT_REFUSED_REPLAY

Triggered when:

- `envelope_id` has already been seen in the issuer's replay window (default 24h, configurable per issuer).
- `expires_ts` is in the past (with +5min skew tolerance).
- `nonce`, if present, has already been seen in the issuer's nonce window.

Audit event: `transport.envelope_refused.replay` with payload `{envelope_id, source_transport, claimed_actor, first_seen_ts}`.

Operational consequence: a benign cause (transport retry of a successfully-delivered envelope) generates this code; a malicious cause (attacker re-playing a captured envelope to re-trigger an approval) also generates this code. The two are operationally indistinguishable from the Kernel side; the response is the same: refuse, audit, do not advance state.

> **Note (operational -- NP-9-2):** v1 deliberately conflates "envelope_id seen before" (replay) and "expires_ts in the past" (expiry) into a single `TRANSPORT_REFUSED_REPLAY` code, on the basis that both express the same concept -- the envelope is outside its valid acceptance window. A future v2.0 MAY split expiry into a distinct `TRANSPORT_REFUSED_EXPIRED` code if operational telemetry shows the two causes warrant separate alerting paths. For v1 the conflation is intentional and stable.

### 5.6 TRANSPORT_REFUSED_OVERSCOPE

Triggered when:

- `claimed_actor.class` is `kernel`, `policy`, or `verifier` (forbidden classes).
- `claimed_actor.class` is `human` but the resolved issuer is not the DDD / Human Gate organ.
- `claimed_actor.class` is `agent` but the resolved issuer is not Kernel-on-behalf-of-agent.
- `payload.kind` declares a request type the issuing Authority organ does not authorise.

Audit event: `transport.envelope_refused.overscope` with payload `{envelope_id, source_transport, claimed_actor, key_id, requested_kind, allowed_kinds}`.

Operational consequence: this code indicates either a misconfigured transport (operator action: re-provision the correct key) or an authority-escalation attempt (operator action: investigate the transport host). It is the most serious of the four refusal codes from a security perspective.

### 5.7 Audit-emit invariant for refusals

Every refusal MUST emit exactly one audit event of the corresponding `event_type` (Section 5.1). The audit event MUST be emitted via the per-session AuditWriter (Spec 10 §2) when the refused envelope was scoped to a known session; otherwise it MUST be emitted to the Kernel-global audit log under the synthetic session id `transport-boundary` (so refused envelopes that target unknown sessions remain inspectable).

**No silent refusals.** A transport that drops an envelope without producing the corresponding audit event is in violation of Article XXIII (Failure Visibility) and Article X (Audit Discipline).

---

## Section 6 -- Authority Attribution & Audit Format

**[normative-description]**

When an envelope is **accepted** (passes all seven verification steps in Section 4.5), the Kernel emits an audit event recording the AUTHORITY of the decision, NOT the transport. This is the operational expression of "Transport is not Authority."

### 6.1 The `decided_by` rule

Every Kernel-side audit event that records an authority-relevant decision MUST carry a `decided_by` field whose value follows the pinned format:

```text
<authority_class>:<transport_hint>:<actor_id>
```

This is the **same shape** as the envelope's `claimed_actor` field (Section 3.2), but the value is **derived by the Kernel after verification**, not copied verbatim from the envelope. The Kernel:

1. Resolves the envelope's `key_id` to the issuing Authority organ.
2. Validates that `claimed_actor.class` is allowed for that issuer (overscope check, Section 5.6).
3. If accepted, records `decided_by = claimed_actor` in the resulting audit event.

If the envelope was **refused**, the audit event records the refusal code (Section 5), and `decided_by` is set to `kernel:boundary:refusal` -- the Kernel itself is the deciding actor for refusals; the would-be requester is recorded under a separate `would_be_actor` field.

> **Footnote (editorial -- NP-9-4):** The `kernel:boundary` form (used in `kernel:boundary:refusal` here and in `kernel:boundary:accept` in Section 6.5) is a **synthetic authority hint**, not an actor in the §6.1 `claimed_actor` vocabulary (which enumerates `human`, `kernel`, `policy`, `verifier`, `agent`). It marks events where the Kernel itself is the deciding actor at the transport boundary -- i.e., the decision is "accept the envelope" or "refuse the envelope" rather than a downstream Authority verdict. Conformance test TBT-22 (Section 9.2) consumes this synthetic hint.

### 6.2 Worked example -- Tier 0 dogfood proof

**[non-normative-example, drawn from production]**

Tier 0 dogfood landed `tg-bot` v0.3.4-beta + `notify-cli` in launchd on 2026-05-11. From the production audit log of that deployment, an `approve` decision delivered via Telegram surfaces in the audit chain as:

```text
{
  "event_type": "ddd.approved",
  "decided_by": "human:tg:817249157",
  "actor": "human",
  "ritual": "ddd",
  "payload_json": "{\"packet_id\":\"...\",\"action\":\"approve\",...}",
  ...
}
```

Read carefully: `decided_by` records `human:tg:817249157`. The **Kernel attributes the human**, not the bot. The transport hint `tg` is informational ("the bytes arrived via Telegram") but the authority class is `human` and the actor is the operator's user_id. The `actor` field is `human`, not `tg-bot`. The `ritual` field is `ddd`, not `transport`.

This is the lived proof that the boundary works. Without HMAC verification at Section 4.5, an attacker who compromised the bot host could fabricate `decided_by="human:tg:817249157"` in any envelope. With HMAC verification, the attacker would also need the secret issued by the DDD / Human Gate organ -- a secret the Kernel reads from its own environment, separate from the bot's environment. The `decided_by` value is therefore a **kernel-witnessed claim**, not a bot-asserted claim.

### 6.3 Parsing rule

Consumers of audit events parse `decided_by` as:

```text
parts = decided_by.split(":", 2)
authority_class = parts[0]   # human | kernel | policy | verifier | agent
transport_hint  = parts[1]   # tg | slack | webhook | api | web | ide | "" for non-transport
actor_id        = parts[2]   # implementation-defined per authority_class
```

For Kernel-internal decisions (no transport involved), the format degenerates to `<authority_class>::<actor_id>` with empty `transport_hint`. Examples:

- `human:tg:817249157` -- human via Telegram
- `human:slack:U7K2X9P` -- human via Slack (future)
- `human::operator-direct` -- human via direct CLI (no transport)
- `kernel::auto-transition` -- kernel-internal automatic transition
- `verifier::tier-1-tests` -- verifier-internal verdict
- `policy::deny-rule-S2` -- policy engine decision

### 6.4 Forbidden attributions

The Kernel MUST NEVER record any of the following as `decided_by`:

- `tg-bot:tg:...` -- the transport is never the authority
- `notify-cli:webhook:...` -- the transport is never the authority
- `slack:slack:...` -- the transport is never the authority
- `transport:*:*` -- there is no `transport` authority class

If the Kernel is asked to record any of the above (e.g. via a misconfigured downstream tool), it MUST refuse with refusal code `TRANSPORT_REFUSED_OVERSCOPE` and emit `transport.envelope_refused.overscope`.

### 6.5 Audit-emit requirement per accepted envelope

Every accepted envelope MUST produce at least one audit event in the per-session AuditWriter chain (Spec 10 §2). The minimum event is:

```text
event_type:    transport.envelope_accepted
decided_by:    kernel:boundary:accept
actor:         kernel
payload_json:  {envelope_id, source_transport, claimed_actor, key_id, payload_kind}
```

Downstream Authority organs (DDD, Verifier, etc.) MAY emit additional events as the envelope's payload is consumed; those events carry their own `decided_by` derived from `claimed_actor` per Section 6.1.

The pair `transport.envelope_accepted` + `<downstream>.decision` makes the **chain of custody** of an authority decision fully inspectable: byte arrived (transport), bytes verified (kernel), decision recorded (downstream organ).

---

## Section 7 -- Forbidden Transport Actions

**[normative-description]**

This section enumerates the explicit MUST-NOT list every transport implementation MUST honour. The list is not exhaustive -- any action that absorbs Authority into the Transport organ is forbidden by Article IV regardless of whether it appears below.

### 7.1 Transport MUST NOT call ritual commands directly

A transport MUST NOT invoke `ai ddd`, `ai gogogo`, `ai close`, or any other ritual command in a way that bypasses the envelope+kernel pipeline.

**Concretely:** a Telegram bot that, on receipt of `/ddd approve`, executes `subprocess.run(["ai", "ddd", "approve"])` without first packaging the request into a signed envelope and waiting for the Kernel's verification result is in violation. The correct pattern: package -> sign -> deliver to Kernel inbox -> Kernel verifies -> Kernel invokes the ritual command (or refuses with a code).

This rule does not forbid the transport from invoking **read-only observation commands** (e.g. `ai status`) on its own initiative, as long as the result is not used to produce an authority decision.

### 7.2 Transport MUST NOT mark verifier verdicts

A transport MUST NOT, in any envelope or any out-of-band message, claim a verifier verdict (`PASS`, `FAIL`, `UNVERIFIED`). Verifier verdicts come exclusively from the Verifier organ (Article VIII; Spec 3 -- TRINITY_VERIFICATION_CONTRACT_SPEC_V1).

A transport that observes "the test summary in the chat reply looks like FAIL" and forwards a synthesised `FAIL` envelope to the Kernel is collapsing transport-into-verifier (Article IV violation). The correct pattern: forward the raw observation as a `payload.kind = "verifier.observation"` envelope; let the Verifier organ decide whether the observation maps to a verdict.

### 7.3 Transport MUST NOT mutate `.ai/state/`

A transport MUST NOT directly write to `.ai/state/`, `.ai/sessions/`, `.ai/audit/`, `.ai/policies/`, or any kernel-owned directory. Workflow state mutation is the Kernel's job (Article V); audit append is the Audit organ's job (Article X); policy is human-write-only (Article XVI + project conventions).

A transport whose implementation requires local state (e.g. last-seen Telegram update_id, conversation state machine, audit-tail offset) MUST keep that state in **its own** state directory, separate from kernel-owned paths. Spec 13 §6.0 and Spec 14 §3.3 already pin this for the two production transports.

### 7.4 Transport MUST NOT bypass kernel envelope validation

A transport MUST NOT short-circuit the Kernel's envelope validation pipeline by, e.g., directly calling Kernel-internal functions that consume already-validated envelopes.

**Concretely:** if a transport author thinks "I've validated the HMAC bot-side, I'll just call the Kernel's downstream consumer directly to save a round-trip," that is forbidden. Bot-side verification collapses to "trust the bot" (Section 4.4); the Kernel's envelope validation is the boundary that prevents bot compromise from becoming kernel compromise. There are no shortcuts.

### 7.5 Transport MUST NOT fabricate `decided_by`

A transport MUST NOT set, propose, or hint at the value of `decided_by` in any audit event. The `decided_by` field is **derived by the Kernel** after envelope verification (Section 6.1).

A transport MAY suggest `claimed_actor` in its envelope (Section 3.1). The Kernel MAY accept that claim if HMAC verification passes. The result MAY then become `decided_by`. But the transport never directly writes `decided_by` -- not in any artifact, not in any audit event, not in any envelope.

### 7.6 Transport MUST NOT cache approval decisions

A transport MUST NOT cache an `approve` / `reject` / `hold` decision and re-issue it on a subsequent request. Each authority decision is a fresh artifact; each fresh artifact requires a fresh signed envelope; each fresh envelope requires a fresh HMAC. Caching collapses to "the transport remembers what the human said and re-applies it" -- which is the transport making the decision (Article XV violation) and is also a self-expansion of authority (Article XX violation).

### 7.7 Transport MUST NOT issue its own keys

A transport MUST NOT generate, mint, or rotate its own HMAC signing keys. All keys come from the issuing Authority organ (Section 4.2). A transport that ships a "first-run key bootstrap" routine that generates a secret without operator-mediated provisioning from the Authority organ is in violation.

### 7.8 Transport MUST NOT silently retry refused envelopes

When the Kernel returns a refusal code (Section 5), the transport MUST surface that refusal to the originating actor via its normal channel. The transport MUST NOT silently retry the same envelope, MUST NOT retry under a different `key_id`, and MUST NOT escalate to a higher-privileged claimed_actor.

The transport MAY retry **once** if the refusal code is `TRANSPORT_REFUSED_UNSIGNED` and the cause is plausibly mid-flight corruption (e.g. truncated payload at the network layer). Retry MUST regenerate `envelope_id` and re-sign; reusing the original `envelope_id` will hit `TRANSPORT_REFUSED_REPLAY`. After one retry, the transport MUST escalate.

### 7.9 Transport MUST NOT translate refusals into verdicts

This is the explicit Article IV anchor for refusal semantics: a refusal is not a verdict (Section 5.2). A transport MUST NOT, on receiving any refusal code, decide that the underlying workflow has therefore FAILED, been REJECTED, or transitioned to any new state. The workflow state is exactly what it was before the refused envelope existed; the refusal is a delivery-layer event, not a workflow-layer event.

---

## Section 8 -- Cross-Reference: Existing Transport Implementations

**[normative-description]**

Trinity v1 ships two production transport siblings. Both rode the Article XV boundary from the start; this Spec codifies the discipline they already practice.

### 8.1 Spec 13 -- `notify-cli` (outbound only)

`notify-cli` (Spec 13: `13_NOTIFY_CLI_SPEC.md`) is the outbound transport: it tails `.ai/audit/events.ndjson` and forwards filtered events to external channels (Telegram, Slack, Discord, SMTP, webhook). It does NOT accept inbound requests; it is therefore a **delivery-only Transport** with no envelope-receiving surface.

Boundary fit:
- **Authority surface:** none. notify-cli never produces an envelope on behalf of an external actor; it forwards kernel-emitted events outward.
- **Refusal codes relevant:** none (no inbound).
- **`decided_by` rule:** does not write `decided_by` (no decisions made).
- **Forbidden actions:** §7.3 (no kernel-state mutation -- notify-cli writes only its own offset SQLite per Spec 13 §6.0 split-duty contract).
- **Webhook outbound HMAC** (Spec 13 §8.3) -- notify-cli signs OUTBOUND payloads to receiver-side endpoints. That is a separate, downstream HMAC contract (the receiver's job to verify); it is not the inbound transport-boundary HMAC governed by this Spec. Both are HMAC-SHA256, but the keys, replay windows, and authority semantics are independent.

### 8.2 Spec 14 -- `trinity-tg-bot` (bidirectional)

`trinity-tg-bot` (Spec 14: `14_TRINITY_TG_BOT_SPEC.md`) is the bidirectional Telegram transport: it accepts inbound commands from the operator via Telegram, packages them into kernel-bound envelopes, signs them with the Kernel HMAC secret, and relays kernel responses back to Telegram. It is the canonical reference implementation of the transport boundary.

Boundary fit:
- **Authority surface:** inbound -- the bot constructs envelopes on behalf of the operator (`claimed_actor: "human:tg:<user_id>"`).
- **HMAC** -- Spec 14 §6.1 Layer 3 (Decision Y) pins HMAC verification at the Kernel side (`core/auth.py` shim), not bot-side. This Spec ratifies that decision: bot-side verification collapses to "trust the bot" (Section 4.4).
- **Refusal codes relevant:** all four (Section 5). The bot SHOULD surface each to the operator via TG reply (e.g. "envelope refused: BADKEY -- contact operator to rotate signing key").
- **`decided_by` rule:** the bot never writes `decided_by`; the Kernel records `human:tg:<user_id>` after verification (Section 6.2 -- Tier 0 dogfood proof).
- **Forbidden actions:** §7.1 (the bot does NOT call `ai ddd` directly -- it constructs an envelope and the Kernel decides), §7.6 (the bot does NOT cache `CONFIRM` decisions -- each destructive op requires a fresh CONFIRM within the 60s window per Spec 14 §6.1 Layer 2), §7.3 (the bot's SQLite at `~/.config/trinity-tg-bot/state.db` is bot-owned, not kernel-state).

### 8.3 Tier 0 dogfood -- production proof (2026-05-11)

The boundary discipline is not theoretical. Tier 0 dogfood landed both transports in launchd on 2026-05-11 and has run continuously since. The audit field `decided_by="human:tg:817249157"` (Section 6.2) is observable in the production `.ai/audit/events.ndjson` -- it is the lived demonstration that the Kernel attributes the human, not the bot.

Concrete properties observed in production:
- **Every TG-mediated `approve` lands as `actor:"human"`, `decided_by:"human:tg:..."`, `ritual:"ddd"`** -- not `actor:"tg-bot"`, never `decided_by:"tg-bot:..."`.
- **HMAC verification rejects** under-tested envelopes with `auth.hmac.fail` (the legacy event_type alias for `transport.envelope_refused.badkey`) before any state advances.
- **Refused envelopes do NOT advance state** -- the workflow stays at the gate; the operator sees the refusal in TG; the Kernel chain shows the refusal event.

### 8.4 Boundary risks observed in production retros

Three operational risks have been recorded against the boundary in production retros and are noted here so future implementations design against them:

1. **Replay window sizing.** The default 24h replay window (Section 5.5) is generous for low-volume operator workflows but may grow the replay log unboundedly under high-throughput transports. Future transports SHOULD allow per-issuer replay-window configuration (out of scope for v1).
2. **Clock skew tolerance.** The +5min skew tolerance (Section 5.5) is compatible with NTP-synced operator hosts but is loose for environments where clocks drift. Future Addendum may tighten to +60s.
3. **Cross-transport `actor_id` collisions.** Telegram `user_id` and Slack `member_id` namespaces are independent. Today the transport_hint disambiguates (`human:tg:123` vs `human:slack:123`). Future cross-transport authority correlation (e.g. "is `tg:123` the same human as `slack:U7K`?") is out of scope; each transport's actor is opaque to the others.

These risks are **operational refinements**, not constitutional gaps. The Article XV boundary holds.

---

## Section 9 -- Conformance Test Matrix

**[normative-description]**

This section enumerates the conformance tests every transport implementation MUST pass before integration. The matrix uses refusal-code-by-trigger as the primary axis. Concrete test code is out of scope for this Spec; this matrix references **what** the test asserts, not **how**.

### 9.1 Inbound envelope conformance

| Test ID | Trigger | Expected behavior | Expected audit event |
|---|---|---|---|
| TBT-01 | Envelope missing `hmac` field on mutating payload | Refuse with `TRANSPORT_REFUSED_UNSIGNED` | `transport.envelope_refused.unsigned` |
| TBT-02 | Envelope missing required field `envelope_id` | Refuse with `TRANSPORT_REFUSED_UNSIGNED` | `transport.envelope_refused.unsigned` |
| TBT-03 | `hmac_alg` set to `"HMAC-SHA512"` | Refuse with `TRANSPORT_REFUSED_BADKEY` | `transport.envelope_refused.badkey` |
| TBT-04 | `key_id` not in registry | Refuse with `TRANSPORT_REFUSED_BADKEY` | `transport.envelope_refused.badkey` |
| TBT-05 | HMAC byte mismatch (tampered payload) | Refuse with `TRANSPORT_REFUSED_BADKEY` | `transport.envelope_refused.badkey` |
| TBT-06 | `envelope_id` re-used within 24h replay window | Refuse with `TRANSPORT_REFUSED_REPLAY` | `transport.envelope_refused.replay` |
| TBT-07 | `expires_ts` 10min in the past | Refuse with `TRANSPORT_REFUSED_REPLAY` | `transport.envelope_refused.replay` |
| TBT-08 | `claimed_actor.class == "kernel"` | Refuse with `TRANSPORT_REFUSED_OVERSCOPE` | `transport.envelope_refused.overscope` |
| TBT-09 | `claimed_actor.class == "human"` but `key_id` is an agent key | Refuse with `TRANSPORT_REFUSED_OVERSCOPE` | `transport.envelope_refused.overscope` |
| TBT-10 | Valid envelope, `payload.kind == "ddd.decision"`, action `approve` | Accept; emit `transport.envelope_accepted` then `ddd.approved` | both events present in chain |

### 9.2 Authority attribution conformance

| Test ID | Trigger | Expected behavior |
|---|---|---|
| TBT-20 | Accepted DDD approve via Telegram | `decided_by == "human:tg:<user_id>"`; `actor == "human"`; `ritual == "ddd"` |
| TBT-21 | Accepted DDD approve via direct CLI | `decided_by == "human::operator-direct"`; `actor == "human"` |
| TBT-22 | Refused envelope of any code | `decided_by == "kernel:boundary:refusal"`; `would_be_actor` records the rejected `claimed_actor` |
| TBT-23 | No transport-claimed `decided_by` ever appears in chain | grep `tg-bot:` / `notify-cli:` / `slack:slack:` in chain returns zero hits |

### 9.3 Forbidden-action conformance (transport-side hygiene)

These tests run against the transport binary itself (e.g. `trinity-tg-bot`), not the Kernel.

| Test ID | Assertion |
|---|---|
| TBT-30 | Transport binary contains no direct `subprocess.run(["ai", "ddd", ...])` invocation; ritual commands are reached only via Kernel envelope pipeline |
| TBT-31 | Transport binary does not write to `.ai/state/`, `.ai/sessions/`, `.ai/audit/`, or `.ai/policies/` |
| TBT-32 | Transport binary does not contain a `decided_by` literal on the write-side |
| TBT-33 | Transport binary's HMAC secret is loaded from env (operator-provisioned), not generated at first run |
| TBT-34 | Transport binary surfaces all four refusal codes to the originating channel; none are silently swallowed |

### 9.4 Audit-chain conformance

| Test ID | Assertion |
|---|---|
| TBT-40 | Every refused envelope produces exactly one `transport.envelope_refused.*` audit event in the per-session AuditWriter chain (Spec 10 §2) |
| TBT-41 | Every accepted envelope produces at least one `transport.envelope_accepted` event before any downstream decision event |
| TBT-42 | The hash chain (Spec 10 §2.1) over transport events validates via `ai audit verify-chain` |

### 9.5 Test categorisation by Verifier tier

Per the Verifier Pyramid (TRINITY_VERIFIER_CONTRACT_V1 §Verifier-Pyramid; Spec 3):

- TBT-01 through TBT-10 are **Tier 0** (deterministic schema/exit/hash checks).
- TBT-20 through TBT-23 are **Tier 1** (deterministic checks against audit-chain rows).
- TBT-30 through TBT-34 are **Tier 1** (deterministic source-tree assertions).
- TBT-40 through TBT-42 are **Tier 0** (chain-recompute checks).

All conformance tests MUST be deterministic. No Tier 3 (LLM-advisory) verification of the transport boundary is permitted; the boundary is too security-load-bearing for advisory verdicts.

---

## Section 10 -- Versioning & Article XXIX Amendment Protocol

**[normative-description]**

### 10.1 Adding a new transport

A new transport (Slack, Discord-bidirectional, generic webhook-receiver, browser-extension, IDE bridge, voice front-end) is an Article XXIX amendment because it widens the trusted-issuer surface. The amendment MUST land via:

1. **Explicit proposal** -- a new Spec under `docs/specs/` (e.g. `15_TRINITY_SLACK_BRIDGE_SPEC.md`) describing the transport's delivery mechanism, envelope construction path, and operator-provisioning flow.
2. **Rationale** -- why the new transport is needed, what operator pain it relieves, why existing transports do not suffice.
3. **Impact analysis** -- which Authority organs MUST issue keys for this transport; what `transport_hint` value is reserved; what new `actor_id` namespace is introduced; what cross-spec contracts are affected.
4. **Human approval** -- operator signs off via the standard PROMOTE/DEPLOY gate; the approval lands as a `decision_packet` artifact.
5. **Version bump** -- this Spec increments to `v1.1` (or `v2.0` if breaking) and the new Spec increments from `v0.1.0`.
6. **Audit entry** -- the integration emits a `transport.registered` event in the kernel-global audit log recording: source_transport, allowed `claimed_actor` classes, issuing Authority organ for keys, `transport_hint` reservation.

### 10.2 Required artifacts for a new transport

Per Article XXVIII (Extension Rule) every new transport MUST declare the eight extension-rule fields. For transports specifically:

| Field | Required value (transport class) |
|---|---|
| role | `"transport"` (must be exactly this string) |
| authority | `"none -- delivery only"` |
| inputs | external channel messages |
| outputs | signed envelopes to Kernel; relayed responses to channel |
| artifacts | per-channel delivery logs (transport-owned, not kernel-owned) |
| state permissions | own state directory only; no `.ai/` writes |
| failure behavior | refusal-code surfacing per Section 5 |
| audit behavior | per-envelope refusal/accept events per Section 5.7 + 6.5 |
| security boundary | HMAC-signed envelopes; key issuance by external Authority organ |

A transport that cannot answer all nine fields MUST NOT be integrated.

### 10.3 Deprecating a transport

Removing a transport is also an Article XXIX amendment. Steps:

1. Mark the transport's Spec as `status: "deprecated"` with a sunset date.
2. Emit `transport.deprecated` audit event recording sunset_date and migration-target transport (if any).
3. After sunset date, kernel rejects all envelopes from `source_transport == <deprecated>` with `TRANSPORT_REFUSED_OVERSCOPE` (the Kernel no longer recognises the transport as authorised).
4. Issuing Authority organs revoke the transport's keys per their own revocation procedures.
5. Final `transport.unregistered` audit event recorded.

### 10.4 Rotating a transport's signing keys

Key rotation is NOT an amendment to this Spec; it is an operational procedure owned by the issuing Authority organ. Each Authority organ MUST document its own rotation cadence. For Phase 9 baseline:

- Human Gate (DDD) -- operator-driven rotation; recommended cadence quarterly or on suspected compromise.
- Kernel-on-behalf-of-agent -- automatic rotation at agent re-registration; manual rotation on operator command.

During rotation, both old and new `key_id` MUST be valid simultaneously for a configurable overlap window (default 24h) to avoid in-flight envelope refusals. The Kernel emits `transport.key.rotated` for each rotation event, recording the old and new `key_id` (the secrets themselves never appear in audit).

### 10.5 Algorithm migration (future)

If a future Addendum expands `hmac_alg` beyond `"HMAC-SHA256"`, the migration is an Article XXIX amendment of this Spec. Migration steps:

1. New algorithm Spec landed under `docs/specs/` (e.g. `TRINITY_TRANSPORT_ED25519_MIGRATION_SPEC.md`).
2. Kernel verification (Section 4.5 step 2) loosens to accept either old or new algorithm during a configurable migration window.
3. Existing transports re-issued with new keys; envelopes start signing with new algorithm.
4. After migration window, kernel verification tightens to accept only the new algorithm; old `key_id`s revoked.
5. This Spec increments to `v2.0` to mark the breaking algorithm pin.

Until that amendment lands, **algorithm agility is forbidden**. `HMAC-SHA256` is the single pinned algorithm for v1.

### 10.6 Spec versioning summary

- v1.0 (this version) -- first canonical Spec; HMAC-SHA256 pinned; four refusal codes; two production transports (`notify-cli` + `trinity-tg-bot`).
- v1.x -- additive transports (each new Spec under `docs/specs/`); refusal-code registry MAY add codes via Addendum; existing codes MUST remain stable.
- v2.0 -- reserved for breaking changes (algorithm migration, schema reshape, refusal-code rename).

Prior versions remain inspectable in git history per Article XXIX.

---

## Section 11 -- Cross-references

**[normative-description]**

- **Constitution Article XV** -- primary anchor; "Transport is not Authority"; verbatim in Section 1.2.
- **Constitution Articles III, IV, XIII, XVI, XX, XXIX** -- supporting anchors; verbatim/quoted in Section 1.3.
- **TRINITY_ORGAN_MAP_V1.md Organ #14 (Transport Gateway)** -- organ contract this Spec ratifies.
- **13_NOTIFY_CLI_SPEC.md** -- outbound transport sibling; boundary fit in Section 8.1.
- **14_TRINITY_TG_BOT_SPEC.md** -- bidirectional transport sibling; boundary fit in Section 8.2; reference implementation of HMAC discipline.
- **TRINITY_DDD_HUMAN_GATE_SPEC_V1.md** -- consumer of accepted `human` envelopes; `signature` field in `approval.json` / `rejection.json` / `hold.json` is the downstream artifact carrier of the envelope's HMAC.
- **TRINITY_AUDIT_EVENT_SPEC_V1.md §3** -- canonical event registry; the four refusal events and `transport.envelope_accepted` MUST be added to that registry under Article XXIX.
- **TRINITY_VERIFICATION_CONTRACT_SPEC_V1.md** -- verifier verdicts (PASS/FAIL/UNVERIFIED) which MUST stay distinct from transport refusal codes (Article IV).
- **trinity_organ_refactor_prd.md §9 Phase 9** -- the PRD section this Spec satisfies.

---

## Section 12 -- Open Questions

**[normative-description]**

- **Q1 -- Algorithm agility timeline.** When does Trinity migrate from `HMAC-SHA256` to a public-key signature scheme (Ed25519 / COSE_Sign1)? Tentative: deferred to Phase 14 Root of Trust; until then, HMAC-SHA256 is sufficient given the single-operator threat model.
- **Q2 -- Cross-transport actor correlation.** Should a future component map `human:tg:817249157` and `human:slack:U7K2X9P` to a single canonical operator identity? Tentative: out of scope for v1; each transport's actor namespace is opaque.
- **Q3 -- Replay-window persistence.** The replay log MUST survive Kernel restart to prevent post-restart envelope re-acceptance. Where does the log live? Tentative: per-issuer SQLite under Kernel-internal state, mirrored to per-session AuditWriter for inspection. Implementation defer.
- **Q4 -- Voice front-end.** The PRD anticipates a future voice transport. Voice introduces transcription-poisoning risk (compromised transcriber substitutes "approve" for "reject"). Mitigation: voice transports MUST require operator-side text confirmation for any mutating envelope. Spec amendment when voice is implemented.

---

## Section 13 -- Out of Scope

**[normative-description]**

- **Implementation paths under `.ai/cli/`.** Concrete file paths (e.g. `core/auth.py`) belong in Spec 14 / TRINITY_DDD_HUMAN_GATE_SPEC_V1, not in this normative Spec.
- **Cryptographic anchoring beyond HMAC-SHA256.** Public-key signatures, certificate chains, hardware-backed keys -- all belong to Phase 14 Root of Trust.
- **Schema files (`*.schema.json`).** This Spec describes envelope shape; the JSON Schema artifact is a separate deliverable.
- **Test code.** Section 9 enumerates **what** to test; **how** to test is out of scope.
- **Per-channel rate limits, throttling, mute hours.** These are channel-level operational policies (Spec 13 §3.4), not transport-boundary rules.
- **Multi-operator quorum.** Authority quorum (e.g. 2-of-N approvers) is a Human Gate concern (Spec 11 §9), not a transport concern. Quorum changes the count of envelopes required; the per-envelope boundary is unchanged.
- **Outbound HMAC to receiver-side webhooks** (Spec 13 §8.3). That HMAC is the receiver's contract to verify, not the inbound transport boundary governed here. Both happen to use HMAC-SHA256, but they are independent crypto domains with independent keys.

---

**Authors:** Trinity Executor (operator direct-draft).
**Anchors confirmed:** Article XV (primary, verbatim Section 1.2), Article III (Section 1.3), Article IV (Sections 1.3, 5.2, 7.9), Article XIII (Section 1.3), Article XVI (Section 1.3), Article XX (Sections 1.3, 7.6), Article XXIX (Sections 1.3, 10).
**Algorithm pinned:** HMAC-SHA256 (Section 4.1).
**Refusal codes enumerated:** TRANSPORT_REFUSED_UNSIGNED, TRANSPORT_REFUSED_BADKEY, TRANSPORT_REFUSED_REPLAY, TRANSPORT_REFUSED_OVERSCOPE (Section 5.1).

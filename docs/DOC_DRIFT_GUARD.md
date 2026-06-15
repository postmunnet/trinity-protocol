# Doc-Drift Guard

> **Status:** SHIPPED (v1 + v2 + follow-up) · 2026-06-15
> **Code:** `.ai/cli/core/doc_coupling.py` · `.ai/cli/core/fact_drift.py` · `.ai/cli/commands/doc_drift.py`
> **Policy:** `.ai/policies/doc_coupling.yaml`
> **Commits:** `8c976c0` (v1) · `672e88c` (v2 fact-drift) · `7e3de33` (follow-up)

How Trinity prevents documentation from drifting out of sync with the code and
reality it describes — kernel-enforced, evidence-backed, opt-in.

---

## TL;DR

Two complementary mechanisms:

| | **doc-coupling** (v1) | **fact-drift** (v2) |
|---|---|---|
| Kind | **Preventive** · session-scoped · **gate** | **Detective** · continuous · **advisory** |
| Question | "you changed code X — did you update doc Y *this session*?" | "right now, does the doc match reality?" |
| Fires at | `rrr` (blocks RETRO→DONE) | `ai doc-drift --facts` (run anytime, read-only) |
| Detection | content-hash snapshot (sss → rrr) | extract truth vs doc's asserted value |
| Escape | `rrr --accept-doc-debt --reason …` (audited) | n/a (advisory) |

Drift can no longer accumulate **silently** through the normal workflow: every
session that touches coupled code is forced at `rrr` to update the doc or record
an explicit waiver. Standing accuracy can be checked any time with `ai doc-drift`.

---

## The problem

Docs (the atlas, `CLAUDE.md`, `RITUALS.md`, `siblings/REGISTRY.md`, …) **age
silently** — code changes, the doc doesn't follow, and nobody notices until a
reader trusts a stale fact. Real cases this guard was built from: the atlas
asserted *16 siblings* when the truth was *19*, and *88 retros* when the truth
was *120*.

The goal is not "perfect docs" — it is **making drift impossible to keep
silent**: you either update the doc, or you waive it on the record.

---

## Mechanism 1 — doc-coupling (preventive gate)

### 1.1 The manifest — declare the coupling

`.ai/policies/doc_coupling.yaml` (operator-authored, Article III write-locked).
Each entry says "if these code paths change, these docs must be updated in the
same session":

```yaml
- id: close-ritual
  severity: block                 # block | warn | info
  when_changed:                   # globs, project-root-relative (** = recursive)
    - "core/trinity_v2/.ai/cli/commands/close.py"
    - "core/trinity_v2/.ai/cli/core/close_contract.py"
  require_update:
    - "core/trinity_v2/docs/RITUALS.md"
    - "dev/trinity_structure_workflow.html"
  reason: "close ritual behaviour changed; seal/archive doctrine must be updated"
```

**severity** decides the consequence:
- `block` — high-confidence doctrine couplings (ritual shortcodes, graph/terminal
  states, close ritual). Blocks `rrr`.
- `warn` — narrative/reference docs that may legitimately lag (sibling roster).
  Allowed, but audited.
- `info` — surfaced only.

> **Scoping matters.** The `ritual-shortcodes` coupling originally used
> `commands/*.py` and false-triggered on *utility* commands (`doc_drift`,
> `doctor`, `config`). It is now scoped to the actual ritual files
> (`vvv/nnn/gogogo/rrr/ddd/close/sss/lll/aaa.py` + `rituals/**`). When you add a
> coupling, list specific files, not broad globs.

### 1.2 The snapshot — how change is detected (at `sss`)

At session creation, `record_coupling_hashes()`
(`.ai/cli/core/doc_coupling.py`, called from `commands/session.py`) computes the
**sha256** of every file referenced by the manifest and writes them to
`<session>/.state/doc_coupling_hashes.json`.

> **Why content-hash, not `git diff`?** The monorepo root is **not** a git repo,
> so `git diff` is inert there. Content-hash is the primary detector; `git diff`
> is a bonus on git-tracked instances. (Same poka-yoke pattern as the runtime
> pointer-pin pre-flight.)

A file is "changed" when its live hash differs from the stamp (or it is newly
created / deleted). **Backward-compat:** a session created before the snapshot
hook has no stamp file → `compute_changed_set()` falls back to git-only (empty on
a non-git root) = **clean**, never "every file changed".

### 1.3 The gate — enforcement (at `rrr`)

`rrr` runs gates in order; the doc-coupling gate sits right after `forbidden_diff`
(`.ai/cli/commands/rrr.py`):

```
rrr  →  acceptance gate  →  forbidden_diff  →  ★ doc-coupling gate ★  →  metrics  →  RETRO→DONE

doc-coupling gate (core/doc_coupling.py: check()):
  1. changed = compute_changed_set()                  # hash-compare (+ git bonus)
  2. for each coupling:
       triggered = changed ∩ when_changed ?
       if triggered:
         missing = require_update docs NOT in changed  → finding: missing_update
         updated-but-no-changelog                      → finding: missing_changelog
  3. verdict:
       any severity:block finding  → ❌ BLOCK RETRO→DONE  (typer.Exit 5)
       any severity:warn  finding  → ⚠  allow + audit doc_coupling.warning
       else                        → ✅ clean
```

### 1.4 The escape hatch — waiver

When a coupling fires but the operator judges there was no real doctrine change
(e.g. a cosmetic edit), waive it explicitly:

```bash
ai rrr --accept-doc-debt --reason "doc-drift is a utility command, not a ritual shortcode"
```

This is **not** a silent override — it appends `doc_coupling.debt_waived` to the
audit chain with `source: explicit_cli_flag` and the reason. (Mirrors the
`--accept-debt` waiver for unconfirmed-goal debt.)

### 1.5 The changelog requirement

When a coupled doc *is* updated, it must carry a fresh changelog entry — an
**ISO-8601 timestamp with offset + the session id** — not a bare date:

```
2026-06-15T07:42:17+07:00 · session 0001_2026-06-15_… · close-ritual
```

The validator (`_changelog_fresh`) checks the touched doc contains both the
session id and an ISO-8601-with-offset timestamp. HTML docs use a
`data-ts`/`data-session` block; Markdown uses `<!-- trinity:changelog -->`
markers. Defaults live under `defaults:` in the manifest
(`changelog_required`, `timestamp_format: iso8601_with_offset`, `timezone`).

**Per-doc exemption.** Living docs that are edited too often to carry a
per-edit changelog — entrypoints (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`,
`WARP.md`) and the atlas — are listed under `defaults.changelog_exempt`
(globs). They are still **required to be updated** (`missing_update` still
applies); they are only exempt from the changelog-freshness check. Versioned
doctrine docs (`RITUALS.md`, `SHORT_CODES.md`) are **not** exempt.

### 1.6 Safety properties

- **Opt-in:** no manifest → `check()` returns `skipped` → gate is a no-op.
- **Fail-soft:** every read is guarded; a malformed manifest is the only
  fail-loud case (surfaced as a block finding, not a crash).
- **Kernel-source fallback:** the shipped manifest applies to the monorepo and is
  inherited by clients, but its paths reference monorepo files so it is inert for
  client trees (their files never match `when_changed`).

---

## Mechanism 2 — fact-drift (detective check)

### 2.1 The idea — truth vs asserted

`.ai/cli/core/fact_drift.py` compares a fact's **canonical value** (extracted
from the source of truth) against what docs **assert** that value to be. This
catches drift even when *nothing changed this session* — a standing accuracy
check.

```
Fact:
  truth_fn(project_root) → canonical value          # e.g. ls siblings/*/  = "21"
  claim_fn(doc_text)     → value the doc asserts     # e.g. atlas "21 source" = "21"
compare → match ✅ | drift ❌ | unknown •
```

### 2.2 The 5 facts

| fact id | truth source | doc claim (atlas) |
|---|---|---|
| `sibling_source_dirs` | count `siblings/*/` | "N source dirs" |
| `registry_active_tools` | `REGISTRY.md` "N registered" | "N registry-active" |
| `graph_terminal_states` | `standard.yaml` `terminal_states` | "DONE, DEAD" |
| `linked_project_count` | `registry/projects.json` length | "thin ×N" |
| `memory_retro_count` | count `.ai/memory/retros/*.md` | *(defers to live — see 2.4)* |

### 2.3 The command (read-only)

```bash
ai doc-drift --facts            # human table: truth vs each doc's claim
ai doc-drift --facts --json     # machine-readable report
ai doc-drift                    # (no --facts) the session coupling check
```

`ai doc-drift` is **read-only / advisory** — it never mutates state, fires a
transition, or appends a state-changing event. The enforcing gate is in `rrr`.

### 2.4 Robustness rules (learned the hard way)

- **Fail-soft → `unknown`, not false drift.** If a source or a doc claim can't be
  read/parsed, the fact is `unknown`, never a spurious `drift`.
- **Extractors are code, not config.** Brittle HTML/MD regexes live in
  `fact_drift.py` where they stay reviewable — not buried in YAML.
- **Volatile facts defer to live.** `memory_retro_count` grows every `rrr` (seen
  going 119→120 mid-session). Freezing a number in a doc re-drifts immediately,
  so the atlas now **defers to `ai doc-drift --facts`** instead of asserting a
  frozen count → fact-drift reports it `unknown` (honest), not perpetual drift.
  Anchored claim regexes (`N retros indexed`, not bare `N retros`) also avoid
  mis-reading historical stats snapshots as the live claim.

---

## Lifecycle (how it prevents future drift)

```
   ┌─ sss  ──────────  stamp sha256 of manifest-referenced files
   │
work├─ edit code (and, ideally, the coupled docs + changelog)
   │
   └─ rrr  ──────────  doc-coupling gate:
                         touched coupled code without updating its docs?
                         → BLOCK (block) / WARN (warn)
                         → update the doc, or --accept-doc-debt (audited)

anytime: ai doc-drift          → coupling check for the current session
         ai doc-drift --facts  → truth-vs-doc, whole repo (standing accuracy)
```

Why drift can't stay silent:
1. Any session touching doctrine code is **forced** at `rrr` to update the doc or
   record an audited waiver — drift can't accumulate through the normal workflow.
2. `ai doc-drift --facts` checks standing accuracy on demand (drop it in CI or run
   periodically).
3. Changelog entries tie every doc change to a **timestamp + session** — you can
   see *when* and *why* a doc moved.

---

## Extending the guard

- **Add a coupling:** add an entry to `.ai/policies/doc_coupling.yaml`
  (`when_changed` → `require_update` + `severity` + `reason`). No code change.
  List specific files; avoid broad globs.
- **Add a fact:** add a `Fact(...)` to the `FACTS` list in `fact_drift.py` with a
  fail-soft `truth_fn` and per-doc `claim_fn`.

---

## Code map

| Concern | File |
|---|---|
| Coupling manifest | `.ai/policies/doc_coupling.yaml` |
| Coupling loader + checker + snapshot + changelog validator | `.ai/cli/core/doc_coupling.py` |
| sss snapshot hook | `.ai/cli/commands/session.py` (`record_coupling_hashes`) |
| rrr gate + `--accept-doc-debt` | `.ai/cli/commands/rrr.py` |
| Fact registry + compare | `.ai/cli/core/fact_drift.py` |
| `ai doc-drift` / `--facts` | `.ai/cli/commands/doc_drift.py` (+ `cli/main.py`) |
| Tests | `.ai/cli/tests/test_doc_coupling.py` · `test_fact_drift.py` |

---

## Limitations (honest)

- Coupling detects that a **file was touched**, not *what* changed — hence the
  waiver for genuinely cosmetic edits.
- Fact-drift claim regexes are brittle if a doc rephrases; fail-soft (`unknown`)
  contains the blast radius but means some real drift can read as unknown.
- A coupling glob that is too broad false-triggers (we hit this); scope to
  specific files.
- The guard only covers what the manifest/fact-registry declare — it is a
  growing safety net, not a complete one.

---

<!-- trinity:changelog:start -->
- 2026-06-15T14:00:00+07:00 · doc-drift guard v1 + v2 + follow-up shipped (commits 8c976c0 / 672e88c / 7e3de33).
- 2026-06-15T15:10:00+07:00 · session 0001_2026-06-15_15_05_pm_feat-doc-drift-changelog-policy-aidocs · per-doc changelog policy (`defaults.changelog_exempt` for living entrypoints/atlas) + ai-docs/ doc-drift pointer.
<!-- trinity:changelog:end -->

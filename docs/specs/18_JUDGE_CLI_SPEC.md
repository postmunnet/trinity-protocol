# Spec 18 — `judge-cli` sibling

**Status:** Draft v0.3 (judge modes — supersedes v0.2)
**Owner:** yai
**Created:** 2026-05-05 (v0.1) · revised 2026-05-06 (v0.2) · revised 2026-05-09 (v0.3)
**Decision-rule class:** Tier 6-A clear sibling

## v0.3 Changelog
- §5 + §6 NEW: 4 judge panel modes via `--judge-mode` flag (default `tiebreak`)
  - `fast` = 2 judges (claude + gemini, no codex)
  - `default` = 3 judges size-diversity (claude-sonnet + gemini-pro + claude-haiku)
  - `cross-vendor` = 3 true vendors (claude + gemini + codex)
  - `tiebreak` = parallel claude+gemini; if `|Δscore| > tiebreak_threshold` (default 1.0) escalate codex; else avg of 2
- §10 cost guards updated: tiebreak default saves codex token burn (called only on disagreement)
- §16 Codex CLI **viability proven 2026-05-09** with `--skip-git-repo-check` + `--output-last-message=<unique-tmpfile>` flags (clean JSON output) but ~20k tokens/trivial-call → high quota burn → escalation pattern preferred over always-on
- §6 envelope new fields: `judge_mode`, `escalated:bool`, `actual_judges[]`, `tiebreak_threshold`
- Bumps to **v0.2.2-beta**

## v0.2 (superseded — CLI backend dual-mode)

## v0.2 Changelog
- §3 Layout: `lib/llm/{sdk,cli}/` split — sdk/ holds existing SDK wrappers (anthropic+openai+google), cli/ holds NEW CLI shell-out wrappers (claude/gemini/codex)
- §4 Deps: SDK deps unchanged (kept for backwards compat); CLI backend uses `node:child_process` stdlib only (no new npm)
- §5 Verbs: all gain `--backend=cli|sdk` flag (default sdk for compat). Per-call selection via flag, env var (`JUDGE_CLI_BACKEND=cli`), or config
- §6 Envelope: `data.backend` field reports actual backend used; `data.cost_usd` is 0 when `cost_mode=subscription` (CLI backend)
- §11 Library mode: identical envelope shape regardless of backend
- §16 Risks: add CLI version drift (defensive flag fallbacks), CLI output format variance (defensive JSON parser handles raw / fenced / preambled)
- Codex CLI documented as suboptimal for judging (code-focused tool); `KNOWN_LIMITATION` exported in lib/llm/cli/codex.js
- Bumps to **v0.2.0-beta**

## v0.1 (original — superseded)

## 1. Purpose

> **`judge-cli` is not a tool — it is a TRUTH SYSTEM.**

Universal LLM-as-judge engine for Trinity. Provides scoring, critique, comparison,
and consensus for ANY content (SEO meta, code, debate stances, docs, tests, ...).
Read-only by design — judges, never executes fixes.

Used by:
- `seo-genie-cli` — score generated content (replaces in-line score module)
- `debate-cli` (future) — consensus check between debate stances
- `Trinity verifier-rules.yaml` — `layer_3_llm_judge` slot (currently disabled)
- code review automation, doc quality, test quality — future use cases

## 2. Architecture invariant

> Judge = court (read-only, score + explain + suggest). Never executes fixes.
> Caller (generator/worker/Trinity) takes judge's output and decides next action.
>
> Multi-vendor by design: judges MUST differ from generator/caller (anti-collusion).
> next_prompt synthesizer MUST be a separate model from judges (anti-leakage).

## 3. Five truth-system properties

Every verb MUST satisfy these 5:

| # | Property | Mechanism |
|---|----------|-----------|
| 1 | **Deterministic** | rubric version + content hash recorded in envelope |
| 2 | **Auditable** | every call → audit chain + cost ledger + source attribution |
| 3 | **Composable** | CLI subprocess (TOOL_CONTRACT envelope) + Library mode (Node require) |
| 4 | **Unbiased** | judges ≠ generator vendor; next_prompt synth ≠ judge models |
| 5 | **Bounded** | 4-layer budget guard + HARD STOP (no warning, no override mid-call) |

## 4. Layout

```
~/.config/judge-cli/
├── config.yaml                 # default models, thresholds, budget caps
├── secrets/                    # chmod 700
│   ├── anthropic.env           # ANTHROPIC_API_KEY (chmod 600)
│   ├── openai.env              # OPENAI_API_KEY
│   └── google.env              # GEMINI_API_KEY
├── rubrics/                    # USER OVERRIDE (shadows built-in)
│   └── (operator-customized)
├── audit/
│   └── ops.ndjson              # hash-chained
└── budgets/
    ├── daily.json              # cumulative cost per ISO date
    └── tasks.json              # active task budgets

judge-cli/
├── index.js                    # --cmd dispatcher
├── lib.js                      # library entry (require/import for siblings)
├── package.json                # Node 20+, deps: anthropic + openai + google + js-yaml
├── README.md
├── TOOL_CONTRACT.json
├── lib/
│   ├── envelope.js, audit.js, secrets.js
│   ├── llm/
│   │   ├── claude.js, openai.js, gemini.js
│   │   └── cost.js             # 4-layer budget tracker
│   ├── rubric.js               # YAML loader + override resolution + hash
│   ├── synth.js                # next_prompt synthesizer (separate model)
│   └── verbs/
│       ├── score.js            # single judge OR panel
│       ├── panel.js            # explicit multi-judge with strategy
│       ├── compare.js          # pairwise A vs B
│       ├── consensus.js        # are N items converged? (for debate-cli)
│       └── critique.js         # detailed feedback only
└── rubrics/                    # BUILT-IN (versioned, reproducible)
    ├── seo_meta_description.yaml
    ├── seo_title.yaml
    ├── alt_text_wcag.yaml
    ├── article_outline.yaml
    ├── code_review.yaml
    ├── doc_quality.yaml
    └── test_coverage.yaml
```

## 5. Verbs

### 5.1 `score` — single content scoring

```
judge-cli --cmd 'score <content-file> --rubric=<name|path>'

Single judge OR panel (depends on --judges):
  --judges=gpt-4-mini                   # single judge
  --judges=gpt-4-mini,gemini-pro,...    # panel mode
  --strategy=median|avg|majority        # default median; required iff panel
  --threshold=9                         # override rubric default

Output: full envelope (see §6)
```

### 5.2 `panel` — explicit multi-judge

```
judge-cli --cmd 'panel <content> --rubric=<...> --models=claude-haiku,gpt-4-mini,gemini-pro'

Always returns:
  - per-judge raw_scores
  - variance + agreement
  - aggregated score (per --strategy)
  - escalation flag if agreement < 0.7
```

### 5.3 `compare` — pairwise A vs B

```
judge-cli --cmd 'compare <a-file> <b-file> --rubric=<...>'

Output: { winner: "A"|"B", confidence: 0.0-1.0, reasoning, deltas: {...} }
Use case: A/B test SEO variants, code patch comparison, debate response selection
```

### 5.4 `consensus` — are N items converged?

```
judge-cli --cmd 'consensus <items.json> --threshold=0.92'

Input: array of stances/responses/positions
Output: { converged: bool, similarity_matrix: [[...]], gaps: [...], min_pair_sim }
Use case: debate-cli uses this every round; score-loop early-exit on stable
```

### 5.5 `critique` — detailed feedback only (no score)

```
judge-cli --cmd 'critique <content> --rubric=<...>'

Output: { issues, fixes, severity, references_to_rubric }
Use case: when caller wants suggestions but doesn't need numeric score
```

## 6. Output schema (TOOL_CONTRACT v1)

```json
{
  "tool": "judge-cli",
  "tool_version": "0.1.0-beta",
  "schema_version": "1.0",
  "command": "score",
  "action": "judge.score",
  "data": {
    "score": 8.2,
    "max_score": 10,
    "pass": false,
    "threshold": 9,
    "summary": "ดีแล้วแต่ยังไม่เฉียบพอเรื่อง intent และ evidence",
    "breakdown": {
      "clarity": 8, "intent_match": 7,
      "specificity": 7, "actionability": 9, "risk": 9
    },
    "improvements": [
      { "issue": "คำแนะนำยัง general", "fix": "เพิ่ม action ที่แก้ได้ทันที 3 ข้อ", "weight": "high" },
      { "issue": "ยังไม่มี evidence", "fix": "บังคับ cite artifact/log/source", "weight": "medium" }
    ],
    "next_prompt": "Revise this to reach 9/10 by improving specificity and evidence.",
    "raw_scores": [
      { "model": "gpt-4-mini", "score": 8.0, "verdict": "..." },
      { "model": "gemini-pro", "score": 8.4, "verdict": "..." }
    ],
    "variance": 0.16,
    "agreement": 0.92,
    "escalate": false,
    "content_hash": "sha256:abc123...",
    "rubric_source": "built_in",
    "rubric_hash": "sha256:def456...",
    "next_prompt_synth_model": "claude-haiku",
    "cost_usd": 0.05,
    "duration_ms": 1234
  },
  "decided_by": "ai" | "human",
  "audit_event_id": "ulid",
  "ts": "<ISO 8601 UTC>"
}
```

**Critical fields (NEW vs spec 17 in-line score):**
- `pass` (boolean) — fast caller decision
- `threshold` — from rubric or override
- `summary` — one-line for human
- `improvements[]` — actionable diff (issue + fix)
- `next_prompt` — feedback-chain ready (synthesized by separate model)
- `agreement` + `variance` — confidence signal; low agreement → `escalate: true`
- `content_hash` + `rubric_hash` — deterministic ref
- `rubric_source` — `built_in | user_override` for debug

## 7. Rubric format

```yaml
# rubrics/seo_meta_description.yaml
name: seo_meta_description
version: 0.1
scale: 0-10
pass_threshold: 9

criteria:
  clarity:
    weight: 0.2
    description: "อ่านแล้วเข้าใจทันที"
  intent_match:
    weight: 0.25
    description: "ตรง search intent / user intent"
  specificity:
    weight: 0.2
    description: "ไม่ generic มีรายละเอียดเฉพาะ"
  actionability:
    weight: 0.2
    description: "แก้ต่อได้ทันที"
  risk:
    weight: 0.15
    description: "ไม่มี hallucination / claim เกินจริง"

required_output:
  - score
  - pass
  - breakdown
  - improvements
  - next_prompt
```

### 7.1 Rubric resolution (Q1c)

Lookup order (override > built-in):
1. `~/.config/judge-cli/rubrics/<name>.yaml` (user override, shadows everything)
2. `judge-cli/rubrics/<name>.yaml` (built-in)
3. `<absolute-path>.yaml` if `--rubric=/abs/path` given

Envelope records `rubric_source: built_in | user_override` for debug clarity.
Hash fingerprints both built-in and override copies (anti-tamper).

## 8. Multi-judge strategies (Q3)

```yaml
strategy: median        # default; rejects outliers
strategy: avg           # naive average; sensitive to outliers
strategy: majority      # categorical pass/fail vote (binary threshold)
strategy: weighted      # operator weights per model (advanced)
```

Always emit:
- `raw_scores[]` per model
- `variance` (statistical)
- `agreement` = 1 - variance/max_score (normalized 0-1)
- `escalate: true` if `agreement < 0.7` (configurable)

→ low agreement = "judges disagree, don't blindly trust score"

## 9. next_prompt synthesizer (Q4c)

Separate model from judges:
- judges = `[gpt-4-mini, gemini-pro]` (e.g.)
- synth = `claude-haiku` (different family)

Synth prompt template:
```
Given these critique notes from {N} judges:
{merged_issues_and_fixes}

Write ONE concise instruction (<200 chars) that tells a content writer
HOW to revise the content to reach {threshold}/{max_score}. Output the
instruction only, no preamble.
```

→ judge LLM doesn't generate `next_prompt` directly (anti-leakage)
→ swappable model (cheap synth = cost optimize)
→ deterministic prompt template (no judge wording bleeds into next iter)

## 10. Cost guards (Q5) — 4-layer HARD STOP

```yaml
budgets:
  per_call: 0.10           # single LLM call cap
  per_batch: 5.00          # one verb invocation cap
  per_task: 1.00           # explicit operator-set per-task (NEW)
  per_day: 20.00           # daily ceiling
```

### 10.1 per-task budget

Operator can set explicit task budget at invocation:
```bash
judge-cli --cmd 'score ... --task-id=amprohealth-seo-batch --task-budget=2.00'
```

Tracker at `~/.config/judge-cli/budgets/tasks.json`:
```json
{
  "amprohealth-seo-batch": {
    "limit": 2.00,
    "spent": 1.62,
    "remaining": 0.38,
    "started_at": "...",
    "calls_count": 24
  }
}
```

### 10.2 HARD STOP behavior

When ANY budget hit:
1. Reject IMMEDIATE next call (do not start it)
2. Return envelope with `error.code: budget_exhausted`
3. NO warning, NO override mid-batch (force operator restart)
4. Audit emit budget.exhausted event

Operator manually resets via `judge-cli --cmd 'budget reset --task=...'`

## 11. Library mode (Q2c)

For Node siblings (seo-genie-cli, debate-cli) avoiding subprocess overhead:

```javascript
// In seo-genie-cli/lib/loop.js
const judge = require('judge-cli/lib');

const result = await judge.score({
  content: variant,
  rubric: 'seo_meta_description',
  judges: ['gpt-4-mini', 'gemini-pro'],
  strategy: 'median',
  task_id: 'amprohealth-seo-batch',
  task_budget: 2.00
});

if (result.pass) accept(variant);
else feedback_chain.push(result.next_prompt);
```

Library mode:
- Bypasses subprocess (50-150ms saved per call)
- Same envelope shape returned
- Same audit/cost tracking (singleton state)
- Same security model

CLI mode = Trinity gogogo + cross-language siblings + operator REPL
Library mode = hot-path Node-to-Node calls

## 12. Policy modes (read-only / sandbox / danger)

```
default         = read-only        # judge.score does NOT execute fixes
                                    # judge.* never writes to user's files

sandbox         = sandbox-only     # writes to /tmp/judge-cli/<task>/
                                    # for compare verb's diff artifacts

danger          = explicit flag    # NOT applicable to judge-cli (judge never executes)
                                    # reserved for siblings like god-team-cli
```

`judge-cli` itself has NO write-to-user-files mode. Period. The whole sibling
is bounded read-only. `god-team-cli` (separate spec) handles execution paths.

## 13. Acceptance criteria

| # | criterion |
|---|-----------|
| A1 | `score` returns envelope with all NEW fields (pass, threshold, improvements, next_prompt) |
| A2 | `panel` always returns raw_scores + variance + agreement |
| A3 | Low agreement (<0.7) sets `escalate: true` in envelope |
| A4 | Rubric override at `~/.config/judge-cli/rubrics/X.yaml` shadows built-in |
| A5 | `rubric_source` field correctly reports `built_in | user_override` |
| A6 | Library mode (`require('judge-cli/lib')`) returns identical envelope shape as CLI |
| A7 | next_prompt synth uses different model from judges (config refusal if same) |
| A8 | Per-call budget exhausted → exit `budget_exhausted` (no partial result) |
| A9 | Per-task budget tracked across multiple invocations (same task_id) |
| A10 | Per-day budget at `~/.config/judge-cli/budgets/daily.json` increments |
| A11 | secrets/*.env mode 0644 → exit 1 |
| A12 | content_hash + rubric_hash present and SHA256-format |
| A13 | TOOL_CONTRACT v1 Platinum 14/14 |
| A14 | Registered in `TRINITY_LEGACY/.ai/tools.yaml` |
| A15 | `consensus` verb returns similarity_matrix for N≥2 items |
| A16 | `compare` verb returns winner + confidence (pairwise) |

## 14. Phased rollout

| Phase | Scope | Effort |
|-------|-------|--------|
| 1 | Scaffold + envelope/audit/secrets/rubric/cost (4-layer) | 1.5 hr |
| 2 | lib/llm/{claude,openai,gemini}.js + cost integration | 1.5 hr |
| 3 | lib/rubric.js (override resolution + hash + validation) | 1 hr |
| 4 | lib/synth.js (next_prompt synthesizer with separate model) | 1 hr |
| 5 | `score` verb + single + panel mode + strategy + escalate | 1.5 hr |
| 6 | `panel` verb + variance + agreement | 1 hr |
| 7 | `compare` + `consensus` + `critique` verbs | 1.5 hr |
| 8 | Library mode (lib.js entry) + ESM/CJS dual export | 1 hr |
| 9 | 7 built-in rubrics (seo + code + doc + test) | 1.5 hr |
| 10 | Tests (unit + acceptance harness) + Platinum 14/14 + register | 1.5 hr |

**Total: ~14 hr ≈ 1.75 day**

## 15. Out of scope

- judge fixes content (always read-only)
- judge calls debate-cli or god-team-cli (callers compose)
- ML-based scoring (LLM-as-judge only; future spec for ML re-ranker)
- Real-time streaming responses
- Per-criterion specialist judges (one judge model handles all criteria of a rubric; future v0.2)
- Image-input judging (covered by alt-text rubric using vision LLM, not new pattern)

## 16. Risks

| risk | mitigation |
|------|-----------|
| Single-vendor judge bias | panel mode default + cross-vendor enforcement |
| Judge gamed by generator (training overlap) | rotate judges + content_hash + rubric_hash audit |
| Rubric drift (built-in vs override divergence) | hash both, log source |
| Library mode singleton bugs | isolated state per process; tests cover concurrent |
| Budget overshoot via parallel calls | atomic file lock on budget file (advisory) |
| next_prompt leaks judge model bias | separate synth model + deterministic template |
| Low agreement ignored | escalate flag forces caller awareness |
| Rubric YAML schema mismatch | validate at load + fail loud |
| API key leak | chmod 600 + redact list (anthropic/openai/google) |

## 17. Composition examples

### A. seo-genie-cli loop (library mode)
```javascript
const judge = require('judge-cli/lib');
const variant = await generate(...);
const result = await judge.score({
  content: variant,
  rubric: 'seo_meta_description',
  judges: ['gpt-4-mini', 'gemini-pro'],
  task_id: 'amprohealth-seo',
  task_budget: 2.00
});
if (result.data.pass) return variant;
feedback_chain.push(result.data.next_prompt);
```

### B. debate-cli round (CLI mode)
```bash
judge-cli --cmd 'consensus stances.json --threshold=0.92'
# {converged: false, min_pair_sim: 0.78, gaps: [...]}
# debate-cli reads gaps, injects into next round prompts
```

### C. Trinity verifier layer 3 (CLI mode, future)
```yaml
# verifier-rules.yaml
layer_3_llm_judge:
  enabled: true            # was false; turn on after judge-cli ships
  call: judge-cli --cmd 'score ... --rubric=verifier_step_quality'
  escalate_threshold: 0.7
```

### D. Code review (CLI mode, future)
```bash
judge-cli --cmd 'compare patch-a.diff patch-b.diff --rubric=code_review'
```

## 18. Dependencies

- Node 20+ runtime
- `@anthropic-ai/sdk` (^0.30) — Claude as judge OR synth
- `openai` (^4) — GPT-4 as judge OR synth
- `@google/generative-ai` (^0.21) — Gemini as judge OR synth
- `js-yaml` (^4) — rubric loader
- `node:crypto` (stdlib) — hashing
- `node:sqlite` (stdlib) — budget tracking + audit chain

NO `wp` binary, NO `ssh`, NO image-processing deps.

---

*End of spec 18 v0.1*

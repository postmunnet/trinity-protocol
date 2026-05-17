# Spec 17 — `seo-genie-cli` sibling

**Status:** Draft v0.3 (CLI backend addendum — supersedes v0.2)
**Owner:** yai
**Created:** 2026-05-04 (v0.1) · revised 2026-05-05 (v0.2) · revised 2026-05-06 (v0.3)
**Decision-rule class:** Tier 6-A clear sibling

## v0.3 Changelog
- `lib/llm/{sdk,cli}/` split symmetric to judge-cli spec 18 v0.2
- Generator LLMs (claude/gemini/codex) gain CLI shell-out backend; judge calls still go via judge-cli library mode
- `--backend=cli|sdk` flag on all generator verbs (meta-desc/title/outline/rewrite/batch-meta-desc); alt-text vision stays SDK-only in v0.3 (CLI image-attach deferred)
- Cost ledger: subscription mode (cost_usd=0, calls counter) for CLI backend
- Backwards-compat shims at top-level lib/llm/{claude,openai,vision}.js retained
- Bumps to **v0.3.0-beta**

## v0.2 (superseded — judge extraction)

## v0.2 Changelog
- §3 Layout: REMOVE `lib/score/*` (moved to judge-cli per spec 18)
- §3 Layout: REMOVE `rubrics/*` (moved to judge-cli built-in + ~/.config/judge-cli/rubrics/ override)
- §6 Score-loop: refactor to call `judge-cli` (library mode by default for hot-path; CLI mode for cross-process)
- §6 Score-loop: use judge's `next_prompt` directly (no in-genie feedback synthesizer)
- §10 Acceptance A_GENIE updated: tests use judge-cli library mode with mock LLM
- §13 Risks: add "judge-cli unavailable" fallback (graceful refusal, no in-genie scoring fallback)
- §15 Composition examples updated to show judge-cli library calls
- Bumps to **v0.2.0-beta**

## v0.1 (original — superseded)

## 1. Purpose

LLM-driven SEO content generator with **score-loop convergence** until each
output reaches threshold (default 9/10) or hits stop conditions. Composes
with wordpress-cli (spec 15 v0.5+) — consumes audit.json, produces
fixes.json that wp-cli applies.

Stateless from operator's view: each verb takes input, runs LLM gen +
score loop, returns best variant + audit history.

## 2. Architecture invariant

> Sibling = LLM brain. Reads JSON input, calls multiple LLM providers,
> scores via rubric + LLM judge, loops until convergence. Writes
> fixes.json + memory feed. NO direct WP I/O — composes via filesystem.
>
> Multi-vendor by design: generator and judge MUST be different LLM
> providers (anti-collusion).

## 3. Layout

```
~/.config/seo-genie-cli/
├── config.yaml             # default models, thresholds, budget
├── secrets/
│   ├── anthropic.env       # ANTHROPIC_API_KEY (chmod 600)
│   ├── openai.env          # OPENAI_API_KEY
│   └── google.env          # GEMINI_API_KEY (optional)
├── rubrics/                # editable scoring criteria
│   ├── meta_description.yaml
│   ├── seo_title.yaml
│   ├── alt_text_wcag.yaml
│   └── article_outline.yaml
└── audit/
    └── ops.ndjson          # hash-chained call log

seo-genie-cli/
├── index.js                # --cmd dispatcher
├── package.json            # Node 20+, deps: anthropic + openai SDKs
├── README.md
├── TOOL_CONTRACT.json
├── lib/
│   ├── envelope.js, audit.js, secrets.js
│   ├── llm/
│   │   ├── claude.js       # Anthropic SDK wrapper
│   │   ├── openai.js       # OpenAI SDK wrapper
│   │   ├── vision.js       # vision-capable LLM (Claude Opus default)
│   │   └── cost.js         # per-call cost tracker
│   ├── score/
│   │   ├── rubric.js       # YAML rubric loader + deterministic checks
│   │   ├── llm_judge.js    # LLM-based scoring (different vendor)
│   │   └── combined.js     # rubric + LLM blend → 0-10 total
│   ├── loop.js             # the score-loop engine
│   ├── memory.js           # memory-cli index integration
│   └── verbs/
│       ├── meta_desc.js
│       ├── title.js
│       ├── alt_text.js
│       ├── outline.js
│       ├── rewrite.js
│       └── batch_meta_desc.js
└── tests/
```

## 4. Dependencies

- `@anthropic-ai/sdk` (^0.30) — Claude generator + vision
- `openai` (^4) — GPT-4 judge OR fallback generator
- `js-yaml` (^4) — rubric + config parsing
- (optional) `@google/generative-ai` — Gemini as judge alternative

## 5. Verbs

### 5.1 `meta-desc` — single page meta description

```
seo-genie-cli --cmd 'meta-desc --input=<page.json>'

Input (page.json):
{
  "page_id": 35418,
  "url": "https://amprohealth.com/icsi-2/",
  "title": "ทำความรู้จัก ICSI...",
  "content": "...full content...",
  "current_meta_desc": "",          // empty if missing
  "target_keyword": "ICSI",
  "tone": "professional",
  "lang": "th",
  "brand_voice": "medical, factual"
}

Output:
{
  "page_id": 35418,
  "best_variant": "ICSI วิธีช่วยมีลูก หากภาวะมีบุตรยาก ขั้นตอน...",
  "score": 9.3,
  "iter_count": 3,
  "exit_reason": "converged",
  "cost_usd": 0.08,
  "history": [
    {"iter": 1, "variant": "...", "score": 7.2, "feedback": "too long"},
    {"iter": 2, "variant": "...", "score": 8.5, "feedback": "kw at end"},
    {"iter": 3, "variant": "...", "score": 9.3, "feedback": "converged"}
  ]
}

Options:
  --threshold=9              (default 9.0, allow 8-10)
  --max-iter=5               (default 5)
  --budget-usd=0.20          (per-page cap, default $0.20)
  --rubric=meta_description.yaml
  --gen-model=claude-sonnet  (default claude-sonnet)
  --judge-model=gpt-4-mini   (default gpt-4-mini, MUST differ from gen)
  --output-format=json       (json | jsonl | md)
```

### 5.2 `title` — SEO title generation

```
Same shape as meta-desc but for title (50-60 chars optimal in en, ~30 in th).
Different rubric.yaml (title-specific criteria).
```

### 5.3 `alt-text` — vision LLM for image alt

```
seo-genie-cli --cmd 'alt-text --image-url=<url> --context=<page.json>'

Vision LLM (Claude Opus default — vision-capable) describes image,
contextualizes with page content, produces WCAG-compliant alt.

Output: { alt_text, length_chars, wcag_score, ... }
Cost: ~$0.20/call (vision LLMs expensive)
```

### 5.4 `outline` — article outline for new content

```
seo-genie-cli --cmd 'outline --topic=<keyword> --target-length=2000'

Generates structured outline:
{
  "h1_options": [...3 variants...],
  "sections": [
    {"h2": "...", "h3_subtopics": [...], "estimated_words": 300},
    ...
  ],
  "internal_link_opportunities": [...],
  "schema_recommendations": ["Article", "FAQPage"]
}
```

### 5.5 `rewrite` — content rewrite for SEO

```
Input: existing content + audit findings + target keyword
Output: rewritten variant with score-loop

Caveats:
  - Larger context = higher cost (~$0.50-2.00/call)
  - Operator MUST review before applying (use bulk-set --dry-run)
```

### 5.6 `batch-meta-desc` — bulk processing

```
seo-genie-cli --cmd 'batch-meta-desc --input=audit.json --out=fixes.json
                     --tone=professional --lang=th --budget-usd=5'

Input: audit.json (from wp-cli seo audit)
   [{page_id, title, url, content, score, issues, ...}, ...]

Output: fixes.json
   [{page_id, meta_desc: "<generated>", score: 9.3, cost_usd: 0.08}, ...]

Process:
  - Filter pages where issues includes "no-meta-desc" or "meta-desc-short"
  - For each, run meta-desc verb
  - Aggregate: total_cost, mean_score, converged_count
  - Halt if --budget-usd exceeded (return partial)

Pipes directly into wp-cli seo bulk-set:
   batch-meta-desc → fixes.json → wp-cli seo bulk-set --json=fixes.json
```

## 6. Score-loop engine (lib/loop.js)

```
function optimize(input, rubric, threshold=9, max_iter=5, stale_limit=2):
  history = []
  best = null
  stale = 0
  feedback_chain = []
  cost = 0
  
  for iter in 1..max_iter:
    variant = generate(gen_model, input + feedback_chain)
    cost += variant.cost
    
    rubric_score = rubric.score(variant)            // 0-5
    llm_score, per_criterion = llm_judge.score(judge_model, variant, rubric)  // 0-5
    total = rubric_score + llm_score                 // 0-10
    
    history.append({iter, variant, total, breakdown, feedback})
    
    if total > best.score: best = current; stale = 0
    else: stale += 1
    
    if total >= threshold: return Result('converged', best, history, cost)
    if stale >= stale_limit: return Result('stalled', best, history, cost)
    if cost > budget_usd: return Result('budget_max', best, history, cost)
    
    feedback_chain.append(generate_feedback(variant, weakest_criterion))
  
  return Result('escalate', best, history, cost)
```

## 7. Rubric YAML format

```yaml
# rubrics/meta_description.yaml
hard_constraints:           # rubric layer (deterministic, 0 or 1)
  length:
    min: 80
    max: 160
    score: 1
  has_focus_keyword:
    score: 1
    bonus_position_first_30: 0.5
  starts_with_capital:
    score: 0.5
  no_keyword_stuffing:
    max_keyword_freq: 2
    score: 1
  no_truncation_chars:
    score: 1                # don't end with "..."

soft_qualities:             # LLM judge layer (0-1 each)
  relevance:
    weight: 1
    prompt: "Does this describe the page accurately?"
  click_appeal:
    weight: 1
    prompt: "Would a user click through to read this?"
  keyword_naturalness:
    weight: 1
  brand_voice_match:
    weight: 1
  no_generic_filler:
    weight: 1

weighting:
  rubric_weight: 0.5
  llm_weight: 0.5
total_max: 10
threshold: 9.0
max_iter: 5
stale_limit: 2
```

## 8. TOOL_CONTRACT v1 envelope

```json
{
  "tool": "seo-genie-cli",
  "tool_version": "0.1.0-beta",
  "schema_version": "1.0",
  "command": "meta-desc",
  "action": "seo-genie.meta_desc",
  "data": {
    "page_id": 35418,
    "best_variant": "...",
    "score": 9.3,
    "iter_count": 3,
    "exit_reason": "converged",
    "cost_usd": 0.08,
    "models_used": {"gen": "claude-sonnet", "judge": "gpt-4-mini"},
    "history_summary": "i1=7.2 i2=8.5 i3=9.3"
  },
  "decided_by": "ai" | "human",
  "audit_event_id": "ulid",
  "ts": "<ISO 8601 UTC>"
}
```

Every call writes to `audit/ops.ndjson` and may delegate deterministic
artifact ingestion to `memory-cli index`. `memory-cli learn` is a
legacy/non-v0.1 semantic surface and must not be used by Trinity `rrr`.

## 9. Security model

### 9.1 Secrets
- `~/.config/seo-genie-cli/secrets/*.env` chmod 600 enforced
- LLM API keys never logged, redact list applied to audit + envelope
- Per-key cost ledger to prevent runaway

### 9.2 Cost guards
- Per-call: `--budget-usd=N` (default 0.20)
- Per-batch: `--budget-usd=N` for batch-meta-desc (default 5.00)
- Per-day: `~/.config/seo-genie-cli/daily_budget.json` tracker (default 20.00)
- HARD STOP at any threshold; return best-so-far with exit_reason=budget_max

### 9.3 Anti-gaming
- Generator and judge MUST be different LLM providers
- Echo detection: if iter N variant cosine > 0.95 with iter N-1 → flag, force regen
- Devil prompt rotation in feedback_chain (forces variety)

## 10. Acceptance criteria

| # | criterion |
|---|-----------|
| A1 | meta-desc with valid input produces score >= threshold OR exit_reason=stalled/budget_max |
| A2 | Score-loop terminates within max_iter (no infinite loop) |
| A3 | History array includes per-iter score + breakdown |
| A4 | Cost cap respected (budget_usd >= cost) |
| A5 | Generator model != judge model (config refusal if same) |
| A6 | secrets/*.env chmod check (refuse mode 0644) |
| A7 | Rubric YAML loads + validates schema |
| A8 | batch-meta-desc processes input.json → output.json |
| A9 | Memory feed: each call writes memory-cli record |
| A10 | TOOL_CONTRACT Platinum 14/14 |
| A11 | Registered in TRINITY_LEGACY/.ai/tools.yaml |
| A12 | Compose: wp-cli audit → genie → fixes.json shape valid for wp-cli seo bulk-set |

## 11. Phased rollout

| Phase | Scope | Effort |
|-------|-------|--------|
| 1 | Scaffold + envelope/audit/secrets/cost tracker | 1 hr |
| 2 | lib/llm/{claude,openai,vision}.js with cost tracking | 1.5 hr |
| 3 | lib/score/{rubric,llm_judge,combined}.js | 1.5 hr |
| 4 | lib/loop.js (score-loop engine) | 1.5 hr |
| 5 | meta-desc verb + rubric YAML + tests | 1.5 hr |
| 6 | title + alt-text (vision) verbs | 1.5 hr |
| 7 | outline + rewrite verbs | 1.5 hr |
| 8 | batch-meta-desc + memory feed | 1 hr |
| 9 | Platinum + acceptance harness + register | 1 hr |
| 10 | Smoke: 1 page meta-desc gen end-to-end | 30 min |

**Total: ~12 hr ≈ 1.5 day** (efficient single-agent build)

## 12. Out of scope (defer)

- Real-time streaming responses (operator waits for final variant)
- Multi-language batch (one --lang per call)
- A/B test variant generation
- SEO-specific reranking ML model (LLM judge only)
- Image generation (only vision-input for alt text)
- Live SERP-data integration (use seed input, skip serp-cli)

## 13. Risks

| risk | mitigation |
|------|-----------|
| LLM cost runaway | per-call + per-batch + per-day budget caps |
| Score plateau (never converge) | stale_limit + budget_max → return best-so-far |
| Judge collusion (same vendor) | config refusal + cross-vendor enforcement |
| Echo loop (variants identical) | embedding similarity check between iters |
| API key leak via stdout | redact list + chmod 600 |
| Rubric brittle (rule mismatch) | rubrics editable YAML, version-controlled |
| LLM hallucinated facts (rewrite) | low temperature + grounded prompts + operator review |
| Threshold gaming (LLM optimizes for judge) | rotate judge model variants |

## 14. Composition examples

### A. End-to-end SEO content fix (the immediate use case)
```bash
# 1. Audit (wp-cli)
wordpress-cli --cmd 'seo audit amprohealth --post-type=page --out=audit.json'

# 2. Generate fixes (seo-genie-cli)
seo-genie-cli --cmd 'batch-meta-desc --input=audit.json --tone=medical --lang=th --budget-usd=5 --out=fixes.json'

# 3. Operator review
$EDITOR fixes.json

# 4. Apply (wp-cli)
wordpress-cli --cmd 'seo bulk-set amprohealth --json=fixes.json --dry-run'
# review → ลบ --dry-run + เพิ่ม --decided-by=human + --include-production
wordpress-cli --cmd 'seo bulk-set amprohealth --json=fixes.json --decided-by=human --include-production'
```

### B. Single page deep optimization
```bash
wordpress-cli --cmd 'post amprohealth get 35418' > page.json
seo-genie-cli --cmd 'meta-desc --input=page.json --threshold=9.5 --max-iter=8' > result.json
seo-genie-cli --cmd 'title --input=page.json' >> result.json
wordpress-cli --cmd 'seo set amprohealth 35418 --meta-desc="..." --title="..." --decided-by=human'
```

### C. Bulk alt text for media library
```bash
wordpress-cli --cmd 'media amprohealth list --number=200' \
  | jq -r '.media[].source' \
  | xargs -I{} seo-genie-cli --cmd 'alt-text --image-url={} --context-file=context.json'
```

---

*End of spec 17 v0.1*

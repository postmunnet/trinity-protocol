---
title: "Trinity Verifier Specification v1.0 (English)"
subtitle: "Deterministic Judge with file-based rules"
language: English
version: 1.0.0-draft
status: draft
last-updated: 2026-04-28
phase: 4
note: "Translation of ../02_VERIFIER_SPEC.md"
critical-fix: "Judge must have real rules, not AI guessing"
---

# Trinity Verifier Specification v1.0 (English)

> **Verifier (verify-cli) = Trinity's Judge — gives deterministic verdicts based on file rules, not LLM intuition.**

---

## 0. Status

- **Phase:** 4
- **Depends on:** Phase 1 (Tool Contract), Phase 2 (memory-cli)
- **Critical fix from feedback:** Verifier blueprint only said "Judge" — must have real rules

---

## 1. Why a Verifier (= Judge)

### Problem

If we let AI judge itself:
- "Does it pass?" — AI says "yes" to please us
- No evidence — AI fabricates
- Rules not in files — drift guaranteed

### Solution

**Rules in files. Deterministic checks first. Escalate to LLM/human only when needed.**

```text
Pyramid of Judgment:

   ┌─────────────────┐
   │ Human           │ ← last resort
   ├─────────────────┤
   │ LLM Judge (gated)│ ← only when needed
   ├─────────────────┤
   │ Policy Rule     │ ← .ai/policies/*.yaml
   ├─────────────────┤
   │ Verifier (det.) │ ← .ai/policies/verifier-rules.yaml
   └─────────────────┘
```

---

## 2. Verdict Schema

### 2.1 Verdict Types (only 4)

| Verdict | Meaning | Action |
|---------|---------|--------|
| **PASS** | Evidence sufficient + all checks ok | Continue workflow |
| **RETRY** | Recoverable failure (transient/missing evidence) | Loop retries |
| **NEEDS_HUMAN** | Verifier unsure / sensitive op | Escalate to user |
| **DEAD** | Unrecoverable failure (policy violation, exhausted budget) | Terminate, archive |

### 2.2 Verdict Envelope

```json
{
  "ok": true,
  "command": "verify",
  "action": "verify.session",
  "data": {
    "verdict": "PASS" | "RETRY" | "NEEDS_HUMAN" | "DEAD",
    "verdict_reason": "all assertions passed",
    "rule_set": "code_change",
    "checks": [
      { "name": "tests_pass", "status": "ok", "evidence_ref": "artifacts/test-result.json" },
      { "name": "diff_scope_allowed", "status": "ok" },
      { "name": "no_forbidden_pattern", "status": "ok" }
    ],
    "missing_evidence": [],
    "next_action": "proceed",
    "escalation_target": null
  },
  "artifacts": [
    { "type": "file", "path": "verify-report.json", "sha256": "..." }
  ],
  "error": null,
  "meta": { "...": "..." }
}
```

---

## 3. Verifier Rules File

### 3.1 Location & Format

**File:** `.ai/policies/verifier-rules.yaml`
**Format:** YAML
**Authority:** Project team (committed to git)

### 3.2 Top-level Schema

```yaml
version: 1
defaults:
  required_evidence: [user_confirmation]
  retry_budget: 3
  timeout_ms: 30000

verifier_rules:
  <rule_set_name>:
    description: "..."
    required_evidence: [...]
    pass_when: [...]
    retry_when: [...]
    needs_human_when: [...]
    dead_when: [...]
    escalation:
      to: "human" | "policy" | "llm_judge"
      message_template: "..."
```

### 3.3 Built-in Rule Sets (must include)

```yaml
verifier_rules:
  # ─── Default catch-all ───
  default:
    required_evidence: [user_confirmation]
    pass_when: [all_questions_answered, no_assumptions_left]
    retry_when: [missing_evidence]
    needs_human_when: [unclear_intent]
    dead_when: [user_cancelled]

  # ─── Code change verification ───
  code_change:
    description: "Verify code modifications"
    required_evidence:
      - diff
      - test_result
      - forbidden_pattern_check
    pass_when:
      - tests_pass
      - diff_scope_allowed
      - no_forbidden_pattern
      - file_paths_within_sandbox
    retry_when:
      - test_failed
      - missing_test_artifact
      - transient_compile_error
    needs_human_when:
      - production_write
      - schema_change
      - api_breaking_change
    dead_when:
      - forbidden_pattern_found
      - sandbox_violation
      - retry_budget_exhausted

  # ─── Browser interaction ───
  browser_check:
    description: "Verify browser-based assertion"
    required_evidence:
      - screenshot
      - current_url
      - selector_assertions
      - http_status
    pass_when:
      - all_assertions_pass
      - no_console_errors_critical
      - http_status_ok
    retry_when:
      - selector_not_found
      - transient_network_error
      - element_not_yet_visible
    needs_human_when:
      - visual_mismatch_uncertain
      - destructive_action_required
      - captcha_appeared
    dead_when:
      - page_load_timeout
      - persistent_404
      - login_failure

  # ─── Deployment verification ───
  deploy_check:
    description: "Verify deployment outcome"
    required_evidence:
      - http_health_check
      - log_tail
      - smoke_test_result
    pass_when:
      - health_check_ok
      - smoke_tests_pass
      - no_critical_errors_in_log
    retry_when:
      - health_check_5xx_transient
      - log_lag
    needs_human_when:
      - performance_degradation
      - user_reported_issue
    dead_when:
      - rollback_required
      - data_corruption_suspected

  # ─── Memory indexing (rrr → memory-cli index) ───
  memory_promote:
    description: "Verify retrospective before adding to memory"
    required_evidence:
      - frontmatter_valid
      - evidence_artifacts_listed
      - confidence_score
    pass_when:
      - schema_valid
      - confidence_ge_0.7
      - has_evidence
    retry_when:
      - missing_frontmatter_field
      - low_confidence_recoverable
    needs_human_when:
      - contradicts_existing_memory
      - very_low_confidence
    dead_when:
      - schema_invalid_unrecoverable
```

### 3.4 Evidence Type Library

Every check must reference an evidence type from a central library:

```yaml
evidence_types:
  # ─── File-based ───
  diff:
    source: "git diff or patch.diff file"
    parser: "unified-diff"
    required_fields: [file_count, line_count]
  
  test_result:
    source: "test runner output (junit/tap)"
    parser: "junit-xml or tap"
    required_fields: [pass_count, fail_count, error_count]
  
  screenshot:
    source: "browser-cli screenshot artifact"
    file_extension: [png, jpg]
    min_size_bytes: 1000
  
  http_health_check:
    source: "curl --fail output"
    required_fields: [status_code, response_time_ms]
  
  log_tail:
    source: "log file tail (last N lines)"
    required_fields: [error_count, warning_count]
  
  current_url:
    source: "browser-cli eval window.location.href"
    type: "string"
  
  selector_assertions:
    source: "browser-cli assert-* commands"
    type: "array of {selector, expected, actual, ok}"
  
  user_confirmation:
    source: "explicit user input"
    type: "boolean"
  
  frontmatter_valid:
    source: "retro-cli validate"
    parser: "yaml frontmatter"
```

---

## 4. verify-cli Tool

### 4.1 Binary Interface

```bash
verify-cli [universal-flags] --rule-set <name> [--cmd <command>]
```

### 4.2 Commands (verbs)

| Verb | Action namespace | Tier | Purpose |
|------|-----------------|------|---------|
| `verify` | `verify.session` | safe | Run verification with rule set |
| `check` | `verify.check` | safe | Run a single check |
| `list-rules` | `verify.list_rules` | safe | List available rule sets |
| `describe-rule` | `verify.describe_rule` | safe | Show rule details |
| `verify-evidence` | `verify.evidence` | safe | Validate an evidence artifact |
| `dry-run` | `verify.dry_run` | safe | Test rule against fake evidence |

### 4.3 Usage Examples

```bash
# Verify a session against code_change rules
verify-cli --cmd "verify --rule-set=code_change --session=.ai/sessions/active"

# Check a single artifact
verify-cli --cmd "check --evidence=artifacts/test-result.json --type=test_result"

# List available rules
verify-cli --cmd "list-rules"

# Describe a rule
verify-cli --cmd "describe-rule code_change"
```

### 4.4 Response Examples

**PASS verdict:**
```json
{
  "ok": true,
  "command": "verify",
  "action": "verify.session",
  "data": {
    "verdict": "PASS",
    "verdict_reason": "All checks passed",
    "rule_set": "code_change",
    "checks": [
      { "name": "tests_pass", "status": "ok", "evidence_ref": "artifacts/junit.xml" },
      { "name": "diff_scope_allowed", "status": "ok" },
      { "name": "no_forbidden_pattern", "status": "ok" },
      { "name": "file_paths_within_sandbox", "status": "ok" }
    ],
    "missing_evidence": [],
    "next_action": "proceed"
  }
}
```

**RETRY verdict:**
```json
{
  "ok": true,
  "command": "verify",
  "data": {
    "verdict": "RETRY",
    "verdict_reason": "Tests failed (recoverable)",
    "rule_set": "code_change",
    "checks": [
      { "name": "tests_pass", "status": "fail", "details": { "failures": 2 } }
    ],
    "next_action": "retry_after_fix",
    "retry_attempt": 1,
    "retry_budget_remaining": 2
  }
}
```

**NEEDS_HUMAN verdict:**
```json
{
  "ok": true,
  "command": "verify",
  "data": {
    "verdict": "NEEDS_HUMAN",
    "verdict_reason": "Production write requires human approval",
    "rule_set": "code_change",
    "next_action": "ask_user",
    "escalation": {
      "target": "human",
      "message": "About to write to {{PROD_FOLDER}}. Approve? (y/n)",
      "context_files": [".ai/sessions/active/02_PLAN.md"]
    }
  }
}
```

**DEAD verdict:**
```json
{
  "ok": true,
  "command": "verify",
  "data": {
    "verdict": "DEAD",
    "verdict_reason": "Forbidden pattern detected",
    "rule_set": "code_change",
    "checks": [
      { "name": "no_forbidden_pattern", "status": "fail",
        "details": { "pattern": "DROP TABLE", "file": "migrations/001.sql" } }
    ],
    "next_action": "terminate_session",
    "audit_event_ref": "events.ndjson:line:1234"
  }
}
```

---

## 5. Pyramid of Judgment Flow

### 5.1 Decision Tree

```
Trinity loop reaches verify step
  │
  ▼
[Layer 1] verify-cli with deterministic rules
  ├─ ALL checks ok                  → PASS
  ├─ Recoverable fail                → RETRY
  ├─ Unrecoverable + clear fail      → DEAD
  ├─ Sensitive op (e.g. prod write)  → NEEDS_HUMAN
  └─ Verifier unsure                 → escalate to Layer 2
       │
       ▼
   [Layer 2] Policy rule check (.ai/policies/*.yaml)
     ├─ Policy explicitly allows     → PASS
     ├─ Policy explicitly forbids    → DEAD
     └─ Policy silent                → escalate to Layer 3
          │
          ▼
      [Layer 3] LLM Judge (gated)
        - Spawn dedicated LLM call (NOT same context as worker)
        - Provide: rule, evidence, project context
        - Return: structured verdict
        - Audit log: full prompt + response (tamper-evident)
          │
          └─ Verdict from LLM        → PASS / RETRY / DEAD / NEEDS_HUMAN
              │
              ▼
          [Layer 4] Human (if NEEDS_HUMAN)
            - Pause workflow
            - Show: rule, evidence, LLM judgment, options
            - User decides: approve / reject / retry / abort
```

### 5.2 LLM Judge — When Used

**MUST be gated** — only when:
- Layer 1 + Layer 2 are both unsure
- `.ai/policies/llm_judge.yaml` allows for this rule set
- Audit budget allows (cost cap per session)

**MUST log:**
- Full prompt sent to LLM
- Full response
- Decision used
- Human review pointer (for after-action audit)

**MUST NOT:**
- Replace deterministic rules
- Override explicit policy forbid
- Run in same context as worker AI (independence)

### 5.3 Human Escalation Format

```yaml
escalation:
  target: human
  urgency: low | normal | high
  message: |
    Verifier needs your decision.
    
    Rule set: code_change
    Verdict candidate: NEEDS_HUMAN
    Reason: Production write requires approval
    
    Evidence:
    - Files changed: [...]
    - Tests: PASS
    - Diff scope: within sandbox
    
    Options:
    [A] Approve and proceed
    [B] Reject (DEAD)
    [C] Retry with constraints
    [D] Defer to manual review
  
  context_files:
    - .ai/sessions/active/02_PLAN.md
    - artifacts/test-result.json
  
  default_after_timeout: NEEDS_HUMAN  # never auto-PASS
  timeout_seconds: 1800                # 30 min
```

---

## 6. Integration with Trinity Loop

### 6.1 Where Verifier is called

```python
# Pseudo-code in trinity loop
def trinity_loop(goal):
    while not done:
        # ... lll, vvv, nnn, gogogo ...
        
        # After execute, call verifier
        verdict = call_tool('verify-cli', f"verify --rule-set={rule_set}")
        
        if verdict.data.verdict == "PASS":
            # Continue to next step
            transition_state(graph, current_state, "verify_pass")
        elif verdict.data.verdict == "RETRY":
            retry_count += 1
            if retry_count > MAX_RETRY:
                terminate("retry_exhausted")
            # Loop back to execute
        elif verdict.data.verdict == "NEEDS_HUMAN":
            ask_human(verdict.data.escalation)
            # Wait for response, re-verify
        elif verdict.data.verdict == "DEAD":
            terminate("verifier_dead")
            break
```

### 6.2 Graph Transition Authority

verify-cli is `decided_by: verifier` in graph:

```yaml
transitions:
  - from: SANDBOX
    to: DO
    trigger: vvv_pass          # ← verify-cli result
    decided_by: verifier
    require_human_approval: false
```

### 6.3 Multiple Rule Sets per Workflow

```yaml
# .ai/graphs/standard.yaml
states:
  - name: SANDBOX
    on_exit:
      verifier_rule_set: pre_execute
  - name: DO
    on_exit:
      verifier_rule_set: code_change
  - name: VERIFIED
    on_exit:
      verifier_rule_set: deploy_check
```

---

## 7. Audit Trail

### 7.1 Every Verdict → Audit Event

```json
{
  "ts": "2026-04-28T12:34:56.789Z",
  "event": "verify_verdict",
  "tool": "verify-cli",
  "run_id": "run_xyz",
  "rule_set": "code_change",
  "verdict": "PASS",
  "verdict_reason": "All checks passed",
  "checks_summary": { "ok": 4, "fail": 0 },
  "evidence_refs": ["artifacts/test-result.json", "artifacts/diff.patch"],
  "prev_hash": "abc123...",
  "hash": "def456..."
}
```

→ Append to `events.ndjson` (hash-chain per blueprint)

### 7.2 LLM Judge Audit (extra strict)

```json
{
  "ts": "...",
  "event": "llm_judge_invoked",
  "rule_set": "code_change",
  "reason_for_escalation": "verifier + policy unsure",
  "prompt_sha256": "...",
  "prompt_path": ".ai/audit/llm-judge/prompt-xyz.txt",
  "response_sha256": "...",
  "response_path": ".ai/audit/llm-judge/response-xyz.txt",
  "verdict": "PASS",
  "human_review_pending": true
}
```

---

## 8. Self-tests

verify-cli must have:

### 8.1 Unit tests (`tests/harness.js`)
- Parse rule YAML
- Evaluate check predicates
- Verdict computation
- Edge cases (empty evidence, missing rule set)

### 8.2 Golden tests (`tests/golden.js`)
- Run against fixture sessions
- Compare verdicts to expected
- Test all 4 verdict types

### 8.3 Rule sanity tests
- Every rule_set must define all 4 verdict states
- All evidence types referenced must be in library
- No unreachable verdicts

```bash
verify-cli --cmd "lint-rules"
# → Validates verifier-rules.yaml itself
```

---

## 9. Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| AI decides PASS itself | Verifier checks rules + evidence |
| Rule embedded in prompt/code | Rule in `verifier-rules.yaml` |
| Verdict = boolean | Verdict = 4 types (PASS/RETRY/NEEDS_HUMAN/DEAD) |
| Evidence = "I think it works" | Evidence = artifact file with sha256 |
| LLM judge every time | LLM judge only when Layer 1+2 unsure |
| Auto-PASS on timeout | NEEDS_HUMAN on timeout |
| Skip human escalation | Pause workflow, ask user |

---

## 10. Open Questions

1. Rule YAML — use JSON Schema validation on load?
2. Evidence library — bundled in verifier-rules.yaml or separate `evidence-types.yaml`?
3. LLM judge — vendor's LLM (Claude API) or local?
4. Human escalation UX — CLI prompt, file-based, or Slack/email?
5. Retry budget — global per session or per rule set?
6. Verdict cache — re-runnable or invalidate?
7. Evidence freshness — TTL in seconds?
8. Multi-rule verification — combine pass = AND or OR?
9. Rule inheritance — `code_change` extends `default`?
10. Custom evidence types — projects can add their own?

---

## 11. Implementation Sketch

```
verify-cli/
├── index.js                       ← entry (stdin/stdout JSON)
├── lib/
│   ├── rule-loader.js              ← parse YAML, validate
│   ├── evidence-collector.js       ← read artifacts, hash
│   ├── check-evaluator.js          ← run predicates
│   ├── verdict-engine.js           ← compute PASS/RETRY/NEEDS_HUMAN/DEAD
│   ├── escalation.js               ← format human/LLM escalation
│   ├── audit-writer.js             ← append events.ndjson
│   └── checks/                     ← each check predicate
│       ├── tests_pass.js
│       ├── diff_scope_allowed.js
│       ├── no_forbidden_pattern.js
│       └── ...
├── schema/
│   ├── config.schema.json
│   ├── response-v1.schema.json
│   ├── verdict.schema.json
│   ├── verifier-rules.schema.json
│   └── evidence-types.schema.json
├── tests/
│   ├── harness.js
│   ├── golden.js
│   └── fixtures/
└── docs/
    ├── ARCHITECTURE.md
    ├── COMMAND_CONTRACT.md
    ├── RULE_AUTHORING_GUIDE.md
    └── EVIDENCE_TYPES.md
```

---

## 12. Quick Reference

### Verdict cheat sheet
```text
PASS         → continue
RETRY        → loop again (with budget)
NEEDS_HUMAN  → ask user (pause)
DEAD         → terminate (audit)
```

### Pyramid
```text
Verifier (det.) → Policy → LLM Judge (gated) → Human
```

### Authority
```text
Verifier may decide PASS/RETRY/DEAD on its own.
Verifier MUST escalate NEEDS_HUMAN.
LLM Judge usage MUST be audited.
Human is final authority.
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §10 (Pyramid of Judgment)
- [`01_TOOL_CONTRACT.md`](01_TOOL_CONTRACT.md) (verify-cli implements this)
- [`03_GOAL_LOOP_SPEC.md`](03_GOAL_LOOP_SPEC.md) (loop calls verifier)
- [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) (`decided_by: verifier`)

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft addressing critical fix #2 from feedback

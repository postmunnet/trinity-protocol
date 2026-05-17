---
title: "Trinity Goal Tree + Loop Specification v1.0 (English)"
subtitle: "Goal-directed execution with sub-goals, checkpoints, resume"
language: English
version: 1.0.0-draft
status: draft
last-updated: 2026-04-28
phase: 5
note: "Translation of ../03_GOAL_LOOP_SPEC.md"
critical-fix: "Linear loop is not enough — must support goal tree + checkpoints"
---

# Trinity Goal Tree + Loop Specification v1.0 (English)

> **The loop is the heart of "running until done" — not just a run-once script.**
>
> The loop must know: what the goal is · what the sub-goals are · how far we've got · where to resume · when to stop.

---

## 0. Status

- **Phase:** 5
- **Depends on:** Phase 1 (Tool Contract), Phase 4 (Verifier)
- **Critical fix from feedback:** Original blueprint only had a linear loop `lll → vvv → nnn → gogogo → rrr` — not enough for big work

---

## 1. Why Goal Tree

### Linear loop (old) — not enough

```text
user: "Do SEO across the whole site"
→ lll → vvv → nnn → gogogo → rrr → DONE? ❌
```

**Problems:**
- "Whole site" = 50+ pages
- Done with one page ≠ done overall
- No way to track sub-goals
- Restart mid-flow = start over

### Goal Tree (new)

```text
g_001 [epic] "Do SEO across the whole site"
├── g_002 [feature] "Audit current state"
│   ├── g_003 [task] "Crawl sitemap"
│   ├── g_004 [task] "Extract metadata"
│   └── g_005 [task] "Generate report"
├── g_006 [feature] "Fix missing metadata"
│   ├── g_007 [task] "Pages 1-25"
│   └── g_008 [task] "Pages 26-50"
└── g_009 [feature] "Verify + deploy"
    ├── g_010 [task] "Run tests"
    └── g_011 [task] "Deploy + monitor"
```

**Result:**
- Decompose once → sub-goals run in sequence
- Resume precisely — see g_007 done, g_008 pending
- Aggregate verdict — root goal PASS = every leaf PASS

---

## 2. Goal Schema

### 2.1 Single Goal (YAML)

```yaml
goal:
  id: g_007
  type: task                      # epic | feature | task | subtask
  description: "Update metadata on pages 1-25"
  parent: g_006                   # null for root
  status: pending                 # pending | running | done | blocked | dead | needs_human
  
  acceptance_criteria:
    - "all 25 pages have title tag"
    - "all 25 pages have meta description"
    - "no duplicate canonical URLs"
  
  estimated_effort:
    duration_min: 30
    iterations_estimate: 5
  
  decomposition_strategy: ai      # ai | template | manual | none
  decomposition_hints:
    template: "page_seo_update"
    batch_size: 5
  
  risk_level: medium              # low | medium | high
  
  context_refs:                   # links to memory/artifacts
    - "memory:r123_seo_audit_2025_12"
    - "artifact:./audit-report.json"
  
  evidence_required:              # which evidence (verifier rule set)
    rule_set: code_change
  
  retry_budget: 3
  timeout_seconds: 1800
  
  created_at: "2026-04-28T10:00:00Z"
  updated_at: "2026-04-28T10:30:00Z"
  completed_at: null
  
  # During execution
  current_iteration: 0
  failure_count: 0
  last_verdict: null
  artifacts: []
```

### 2.2 Goal Tree (collection)

**Storage:** `.ai/sessions/<session-id>/goals.yaml` (or `goals.json`)

```yaml
version: 1
session_id: "sess_2026-04-28_seo"
root_goal_id: g_001
goals:
  - id: g_001
    type: epic
    description: "..."
    parent: null
    children: [g_002, g_006, g_009]
    status: running
  - id: g_002
    parent: g_001
    children: [g_003, g_004, g_005]
    status: done
  # ... etc
```

### 2.3 Goal Status State Machine

```text
pending  ──┐
           │ trigger: start
           ▼
        running ──┬──→ done
                  │
                  ├──→ blocked        (waiting on dependency)
                  │       │
                  │       └─→ running (when unblocked)
                  │
                  ├──→ needs_human    (verifier escalation)
                  │       │
                  │       └─→ running (after human input)
                  │
                  └──→ dead           (unrecoverable / cancelled)
```

---

## 3. Loop State

### 3.1 `loop_state.json` Schema

**Location:** `.ai/sessions/<session-id>/loop_state.json`

```json
{
  "version": 1,
  "session_id": "sess_2026-04-28_seo",
  "started_at": "2026-04-28T10:00:00Z",
  "updated_at": "2026-04-28T11:30:00Z",
  
  "current_goal": "g_007",
  "current_phase": "EXECUTING",
  
  "queue": {
    "pending": ["g_008", "g_010", "g_011"],
    "running": ["g_007"],
    "done": ["g_002", "g_003", "g_004", "g_005", "g_006"],
    "blocked": [],
    "needs_human": [],
    "dead": []
  },
  
  "iteration": 12,
  "max_iterations": 50,
  
  "budget": {
    "tokens_used": 45000,
    "tokens_max": 200000,
    "duration_ms_used": 1800000,
    "duration_ms_max": 7200000,
    "retry_count": 2,
    "retry_max": 10
  },
  
  "last_verdict": "PASS",
  "last_verdict_ts": "2026-04-28T11:25:00Z",
  
  "checkpoints": [
    { "id": "ckpt_001", "ts": "2026-04-28T10:30:00Z", "goal_id": "g_002", "phase": "DONE" },
    { "id": "ckpt_002", "ts": "2026-04-28T11:00:00Z", "goal_id": "g_006", "phase": "DONE" }
  ],
  
  "termination": {
    "status": "active",
    "reason": null
  }
}
```

### 3.2 Atomic Updates

- Loop state file = **append-only history** + current snapshot
- Update via temp file rename (atomic)
- Every state change → also append to `events.ndjson`

---

## 4. Loop Algorithm

### 4.1 Pseudo-code

```python
def trinity_loop(initial_goal, config):
    # 1. Initialize
    goal_tree = goal_tree_from(initial_goal)
    state = LoopState(goal_tree, config)
    state.persist()
    
    # 2. Main loop
    while not state.terminated():
        # Check budget
        if state.budget_exhausted():
            state.terminate("budget_exhausted")
            escalate_to_human(state)
            break
        
        # Get next goal to execute
        current = state.next_pending_goal()
        if current is None:
            if state.all_done():
                state.terminate("all_goals_done")
            elif state.has_blocked():
                state.terminate("deadlock")
                escalate_to_human(state)
            break
        
        # Execute the goal
        state.mark_running(current.id)
        result = execute_goal(current, state)
        
        # Verify outcome
        verdict = call_tool('verify-cli', f"verify --rule-set={current.evidence_required.rule_set}")
        
        # Apply verdict
        if verdict == "PASS":
            state.mark_done(current.id)
            state.checkpoint()
        
        elif verdict == "RETRY":
            current.failure_count += 1
            if current.failure_count > current.retry_budget:
                state.mark_dead(current.id, reason="retry_exhausted")
            else:
                state.mark_pending(current.id)  # requeue
        
        elif verdict == "NEEDS_HUMAN":
            state.mark_needs_human(current.id)
            response = ask_human(verdict.escalation)
            apply_human_response(current, response, state)
        
        elif verdict == "DEAD":
            state.mark_dead(current.id, reason=verdict.verdict_reason)
            if current.is_critical():
                state.terminate("critical_goal_dead")
                break
        
        # Decompose if needed
        if current.type in ['epic', 'feature'] and current.status == 'done':
            sub_goals = decompose(current, state)
            state.enqueue(sub_goals)
        
        # Persist state
        state.persist()
    
    # 3. Final retro
    call_tool('retro-cli', f"summarize --session={state.session_id}")
    return state.summary()
```

### 4.2 Goal Decomposition

```python
def decompose(goal, state):
    if goal.decomposition_strategy == 'ai':
        # Ask vendor AI to decompose
        sub_goals = vendor_ai_decompose(
            goal=goal,
            context=state.recent_memory(),
            hints=goal.decomposition_hints
        )
    elif goal.decomposition_strategy == 'template':
        sub_goals = load_template(goal.decomposition_hints.template)
    elif goal.decomposition_strategy == 'manual':
        sub_goals = ask_human_to_decompose(goal)
    else:
        return []
    
    # Validate sub-goals (each must have: description, acceptance_criteria, evidence_required)
    return [validate(sg) for sg in sub_goals]
```

### 4.3 Termination Conditions

| Condition | Action |
|-----------|--------|
| All goals done | Success — final retro |
| Budget exhausted (tokens/time/retry) | Escalate human |
| Critical goal DEAD | Terminate + retro |
| Deadlock (all blocked, no progress) | Escalate human |
| Explicit `STOP` signal | Graceful exit + retro |
| Cancelled by user | Cancel + retro |

---

## 5. CLI Commands

### 5.1 Trinity loop CLI

```bash
trinity loop --goal "Do SEO across the whole site" [--config path] [--max-iter N] [--budget tokens=200000]
```

### 5.2 Subcommands

| Command | Purpose |
|---------|---------|
| `trinity loop start --goal "..."` | Start new loop |
| `trinity loop resume --session <id>` | Resume from checkpoint |
| `trinity loop status [--session <id>]` | Show current state |
| `trinity loop pause` | Pause running loop |
| `trinity loop stop --session <id>` | Stop + finalize |
| `trinity loop checkpoint --session <id>` | Manual checkpoint |
| `trinity loop tree --session <id>` | Show goal tree |
| `trinity loop history --session <id>` | Show event history |

### 5.3 Examples

```bash
# Start
trinity loop start --goal "Update Yoast plugin safely" --max-iter=20

# Output:
# session_id: sess_2026-04-28_yoast
# root_goal: g_001
# decomposed into 5 sub-goals
# starting iteration 1...

# Resume after restart
trinity loop resume --session sess_2026-04-28_yoast

# Check progress
trinity loop status
# {
#   "session_id": "...",
#   "current_goal": "g_003",
#   "phase": "EXECUTING",
#   "progress": "3/5 done",
#   "budget_remaining": "55%",
#   "estimated_complete": "2026-04-28T12:00:00Z"
# }

# Show tree
trinity loop tree
# g_001 [epic] "Update Yoast plugin safely" [running]
# ├── g_002 [task] "Backup DB" [done]
# ├── g_003 [task] "Update plugin" [running]
# ├── g_004 [task] "Health check" [pending]
# ├── g_005 [task] "Smoke test" [pending]
# └── g_006 [task] "Notify team" [pending]
```

---

## 6. Sub-goal Queue Strategy

### 6.1 Queue Discipline

- **FIFO** by default (sub-goals in order)
- **Priority** override (high-risk first?)
- **Dependency** respect (sub-goal B depends on A → A first)

### 6.2 Parallel Execution (future v2)

- Some sub-goals can run in parallel (no shared state)
- Trinity kernel locks prevent races
- For v0.1 — sequential only

### 6.3 Skip / Defer

- User can mark goal as `skip` (mark done with reason)
- Or `defer` (move to back of queue)

---

## 7. Checkpoint & Resume

### 7.1 Checkpoint Triggers (auto)

- Every N iterations (config: `checkpoint_every_n=5`)
- Every M minutes (config: `checkpoint_every_minutes=10`)
- After any goal `done`
- Before any `aggressive` policy action
- Manual via `trinity loop checkpoint`

### 7.2 Checkpoint Content

```json
{
  "id": "ckpt_010",
  "ts": "2026-04-28T11:30:00Z",
  "session_id": "...",
  "goal_tree_snapshot": "<sha256 of goals.yaml>",
  "loop_state_snapshot": "<full state>",
  "artifacts_manifest": [
    { "path": "...", "sha256": "..." }
  ],
  "events_offset": 1234   // events.ndjson byte offset
}
```

### 7.3 Resume Logic

```python
def resume(session_id):
    state = LoopState.load(session_id)
    
    # Verify session is resumable
    if state.terminated():
        error("Session is terminated, cannot resume")
    
    # Find latest checkpoint
    ckpt = state.latest_checkpoint()
    
    # Restore artifacts (verify hashes)
    verify_artifacts(ckpt.artifacts_manifest)
    
    # Replay events.ndjson from offset (for missing state)
    state.replay_events(from_offset=ckpt.events_offset)
    
    # Continue main loop
    return trinity_loop_continue(state)
```

### 7.4 Resume Across Process Restart

- All state persisted to filesystem
- No in-memory-only state
- Process can be killed + restarted
- Resume picks up from latest checkpoint

---

## 8. Budget Management

### 8.1 Budget Types

| Type | Unit | Default | Why |
|------|------|---------|-----|
| `tokens` | LLM tokens | 200,000 | API cost cap |
| `duration` | milliseconds | 7,200,000 (2h) | Wall-clock cap |
| `retry` | count | 10 | Avoid infinite loop |
| `tool_calls` | count | 200 | Avoid runaway |
| `iterations` | count | 50 | Goal tree depth cap |

### 8.2 Budget Sources

```yaml
# .ai/policies/loop-budget.yaml
default_budget:
  tokens: 200000
  duration_ms: 7200000
  retry: 10
  tool_calls: 200
  iterations: 50

# Per-goal type override
by_goal_type:
  epic:
    tokens: 1000000
    duration_ms: 14400000
  task:
    tokens: 50000
    duration_ms: 1800000
```

### 8.3 Soft / Hard Limits

- **Soft limit (80%):** Warn + checkpoint
- **Hard limit (100%):** Pause + escalate human

---

## 9. Human Escalation Points

The loop pauses + asks the human at:

1. **Goal decomposition unclear** — show options, ask user to pick
2. **Verifier returns NEEDS_HUMAN** — show evidence, ask decision
3. **Budget approaching limit** — confirm continue or stop
4. **Deadlock detected** — show blocked goals, ask user to resolve
5. **Sensitive op (production write)** — explicit approval each time
6. **Confidence < threshold** — verifier unsure → ask human
7. **Critical failure** — show error, ask retry/abort/escalate

### 9.1 Escalation Output Format

```yaml
escalation:
  type: needs_decomposition
  goal_id: g_005
  message: "Decompose 'Audit SEO' into sub-goals?"
  options:
    - { id: A, label: "Auto-decompose with AI", default: true }
    - { id: B, label: "Use template 'seo_audit_v2'" }
    - { id: C, label: "Manual entry" }
    - { id: D, label: "Skip this goal" }
  default_after_timeout: D
  timeout_seconds: 600
```

---

## 10. Integration with Other Components

### 10.1 With Verifier

- Loop calls verifier after each goal execute
- Verdict drives state transition (PASS/RETRY/NEEDS_HUMAN/DEAD)
- See: [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md)

### 10.2 With Graph

- Loop respects graph state machine
- Each goal traverses graph (READY → VERIFYING → ... → DONE)
- See: [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md)

### 10.3 With Memory

- Loop start: `memory-cli search "<goal>"` → get context
- Loop end: `retro-cli summarize` → `memory-cli index`
- See: [`05_MEMORY_CLI_SPEC.md`](05_MEMORY_CLI_SPEC.md)

### 10.4 With Vendor Harness

- Vendor AI proposes decomposition
- Vendor AI proposes plan (`nnn`)
- Vendor AI executes (`gogogo`) — through CLI tools
- Trinity loop = orchestrator, vendor AI = worker

---

## 11. Anti-patterns

| ❌ Anti-pattern | ✅ Correct |
|-----------------|-----------|
| Single goal string | Goal tree with sub-goals |
| No state persistence | `loop_state.json` + checkpoints |
| Linear execution only | Loop with retry + escalation |
| No budget | tokens/time/retry caps |
| Auto-continue on NEEDS_HUMAN | Pause + ask user |
| Re-decompose every iteration | Decompose once, persist |
| Lose state on restart | Resume from checkpoint |
| Skip verifier | Always verify after execute |

---

## 12. Open Questions

1. Goal storage — YAML, JSON, or SQLite?
2. Decomposition prompt — standardize template?
3. Sub-goal limit per parent — cap?
4. Parallel sub-goals — when supported?
5. Goal types — fix at 4 (epic/feature/task/subtask) or extensible?
6. Budget enforcement — soft warn or hard stop?
7. Resume — should re-validate evidence?
8. Checkpoint format — full state or delta?
9. Cancellation cascade — child goals when parent dead?
10. Inter-session goals — long-running across multiple sessions?

---

## 13. Implementation Sketch

```
.ai/cli/commands/loop.py     ← Trinity kernel loop command
  ├── lib/goal_tree.py
  ├── lib/loop_state.py
  ├── lib/decomposer.py
  ├── lib/budget.py
  ├── lib/checkpoint.py
  └── lib/escalation.py

.ai/sessions/<session>/
  ├── goals.yaml             ← goal tree
  ├── loop_state.json        ← runtime state
  ├── checkpoints/
  │   ├── ckpt_001.json
  │   └── ckpt_002.json
  └── artifacts/
```

---

## 14. Quick Reference

### Goal lifecycle
```
pending → running → (done | blocked | needs_human | dead)
```

### Loop verdict actions
```
PASS         → mark done, next goal
RETRY        → requeue, increment failure
NEEDS_HUMAN  → pause, ask user
DEAD         → mark dead, possibly terminate
```

### Termination reasons
```
all_goals_done | budget_exhausted | critical_goal_dead 
| deadlock | user_cancelled | timeout
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) §4.2 (Loop)
- [`02_VERIFIER_SPEC.md`](02_VERIFIER_SPEC.md) (verdicts)
- [`04_GRAPH_SPEC.md`](04_GRAPH_SPEC.md) (state machine)

## Changelog

- **v1.0.0-draft (2026-04-28)** — Initial draft addressing critical fix #3 from feedback

---
title: "Commit Plan 0–7 — Detailed Execution Spec"
status: locked
last-updated: 2026-04-28
audience: "Executor (human or AI agent)"
purpose: "Step-by-step commit instructions. Each commit must pass acceptance criteria before next."
---

# 3. Commit Plan 0–7

> **Rule:** Acceptance criteria ของ commit N **ต้องผ่าน 100%** ก่อนเริ่ม commit N+1. ห้าม batch.

## Status Overview

| Commit | Status | Time est. |
|--------|--------|-----------|
| 0 — Evidence triage | ✅ DONE | 5 min |
| 1 — Make core runnable | ⏳ ready | 10 min |
| 2 — Phase 0.5 stubs | ⏳ ready | 10 min |
| 3 — Port v2 workflow | 📋 planned | 5 min |
| 4 — Browser-cli contract refs | 📋 planned | 3 min |
| 5 — Knowledge Brain (scrubbed) | 📋 planned | 10 min |
| 6 — Shim references | 📋 planned | 5 min |
| 7 — Brain seed sample | 📋 planned | 10 min |
| **Total** | | **~60 min** |

---

## Commit 0 — Evidence Triage ✅ DONE

**Goal:** ยืนยัน assumptions ก่อน commit ใดๆ

**Output:** [`02_EVIDENCE_TRIAGE.md`](02_EVIDENCE_TRIAGE.md)

**Acceptance:** ✅ `02_EVIDENCE_TRIAGE.md` complete กับ 4 findings

---

## Commit 1 — Make Core Runnable

**Goal:** `bash .ai/cli/ai status` ไม่ fatal + `pytest cli/tests` 14/14 pass + Hash Chain Genesis valid

### Files affected (~12)

| File | Source | Action |
|------|--------|--------|
| `.ai/ssot.yaml` | TRINITY_LEGACY/.ai/ HEAD | Copy + **rewrite paths to relative** (D12) |
| `.ai/requirements.txt` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/policies/safety.yaml` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/policies/gates.yaml` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/policies/rbac.yaml` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/policies/PROTOCOL.md` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/schemas/events.schema.json` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/schemas/plan.schema.json` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/schemas/safety.schema.json` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/schemas/session_state.schema.json` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/schemas/summary.schema.json` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/state/status.json.template` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/state/verify_report.json.template` | TRINITY_LEGACY/.ai/ HEAD | Copy as-is |
| `.ai/testing/canaries/canary_with_secrets.py` | TRINITY_LEGACY/ HEAD | Copy (test fixture) |
| `.ai/audit/events.ndjson` | **NEW** — generate genesis | See sub-task below |

### Sub-tasks (numbered)

1. **Copy from TRINITY_LEGACY HEAD** — ใช้ `git archive HEAD <file>` from `TRINITY_LEGACY/.ai/` ไม่ใช่ working tree (เพราะ ssot.yaml มี modified)
2. **Rewrite ssot.yaml paths** — ตรวจว่า `project_root: "."` (relative) ไม่มี absolute path เหลือ
3. **Generate genesis event** (D9) — สร้าง `events.ndjson` line แรก:
   ```json
   {"ts":"<ISO8601 UTC>","type":"genesis","prev_hash":"0","details":{"trinity_version":"v0.1.0","spec_pack":"v1.0.0","project":"trinity_v2"},"hash":"<sha256>"}
   ```
   - Hash = SHA-256 ของ canonical JSON ของ event นี้ (excluding `hash` field itself)
4. **Test 1:** `cd trinity_v2 && bash .ai/cli/ai status` → ไม่ ImportError, exit 0
5. **Test 2:** `cd trinity_v2/.ai && python3 -m pytest cli/tests -q` → 14/14 pass
6. **Test 3:** Validate genesis hash:
   ```python
   import json, hashlib
   with open('.ai/audit/events.ndjson') as f:
       e = json.loads(f.readline())
       canonical = json.dumps({k:v for k,v in e.items() if k != 'hash'}, sort_keys=True, separators=(',',':'))
       assert e['hash'] == hashlib.sha256(canonical.encode()).hexdigest()
       assert e['prev_hash'] == '0'
       assert e['type'] == 'genesis'
   ```

### Acceptance criteria (must all pass)

- ✅ `bash .ai/cli/ai status` exits 0, ไม่มี Traceback
- ✅ `pytest cli/tests -q` shows `14 passed`
- ✅ Genesis event ใน `events.ndjson` validate ผ่าน sub-task 6
- ✅ `grep -r "<user-home>" .ai/ssot.yaml .ai/policies/ .ai/schemas/` → 0 matches (no absolute paths)

### Spec refs

- `00_BLUEPRINT.md §4` (Hash Chain audit)
- `00b_BOOTSTRAP_PACK.md §3` (template structure)

---

## Commit 2 — Phase 0.5 Stubs

**Goal:** Spec-required stubs (tools.yaml, graphs/, verifier-rules, loop-budget) **with real values** + YAML validation test

### Files affected (~6 new)

| File | Spec ref | Source |
|------|----------|--------|
| `.ai/tools.yaml` | INDEX.md §5.3 | Stub registry (NEW) |
| `.ai/graphs/standard.yaml` | 04_GRAPH_SPEC.md | Stub with `decided_by` everywhere (D10) |
| `.ai/graphs/deploy.yaml` | 04_GRAPH_SPEC.md | Stub with `decided_by` |
| `.ai/policies/verifier-rules.yaml` | 02_VERIFIER_SPEC.md | Pyramid 4 layers (D8) |
| `.ai/policies/loop-budget.yaml` | 03_GOAL_LOOP_SPEC.md | Real values (D11) |
| `.ai/cli/tests/test_yaml_valid.py` | Star Enhancement §3.1 | NEW test |

### Sub-tasks

7. **`tools.yaml`** — empty registry skeleton:
   ```yaml
   version: "1.0"
   tools: []        # populated as tools come online
   ```

8. **`graphs/standard.yaml`** — minimal but with `decided_by` ทุก transition:
   ```yaml
   states: [READY, THINK, SANDBOX, DO, VERIFIED, PROMOTED, DEPLOYED, RETRO, DONE]
   transitions:
     - {from: READY,    to: THINK,     trigger: sss,             decided_by: kernel}
     - {from: THINK,    to: SANDBOX,   trigger: nnn_pass,        decided_by: kernel}
     - {from: SANDBOX,  to: DO,        trigger: vvv_pass,        decided_by: verifier}
     - {from: DO,       to: VERIFIED,  trigger: gogogo_complete, decided_by: verifier}
     - {from: VERIFIED, to: PROMOTED,  trigger: promote_request, decided_by: human, require_human_approval: true}
     - {from: PROMOTED, to: DEPLOYED,  trigger: deploy_request,  decided_by: human, require_human_approval: true}
     - {from: DEPLOYED, to: RETRO,     trigger: rrr,             decided_by: kernel}
     - {from: RETRO,    to: DONE,      trigger: rrr_complete,    decided_by: kernel}
   ```

9. **`graphs/deploy.yaml`** — deploy-only subgraph (similar pattern, `decided_by: human` for prod transitions)

10. **`verifier-rules.yaml`** — Pyramid 4 layers:
    ```yaml
    version: "1.0"
    pyramid:
      layer_1_deterministic:
        rules_file: .ai/policies/verifier-rules.yaml
        coverage_target_pct: 80
        rule_sets: []   # populated in Phase 4
      layer_2_policy:
        gates_file: .ai/policies/gates.yaml
        safety_file: .ai/policies/safety.yaml
      layer_3_llm_judge:
        enabled: false        # gated, last resort
        audit_required: true
        max_calls_per_session: 3
      layer_4_human:
        verdict: NEEDS_HUMAN
        timeout_minutes: 60
    verdicts: [PASS, RETRY, NEEDS_HUMAN, DEAD]
    ```

11. **`loop-budget.yaml`** — real values:
    ```yaml
    version: "1.0"
    default_budget:
      max_iterations: 20
      max_duration_minutes: 30
      max_tool_calls: 100
      checkpoint_every: 5
    escalation:
      on_iterations_exceeded: NEEDS_HUMAN
      on_duration_exceeded: NEEDS_HUMAN
      on_tool_calls_exceeded: NEEDS_HUMAN
    overrides: {}     # per-graph overrides go here
    ```

12. **`test_yaml_valid.py`** — Star's enhancement (§3.1):
    ```python
    import glob, yaml, pytest

    @pytest.mark.parametrize("path", glob.glob(".ai/policies/*.yaml") + glob.glob(".ai/graphs/*.yaml"))
    def test_yaml_loadable(path):
        with open(path) as f:
            yaml.safe_load(f)

    def test_graphs_have_decided_by():
        for path in glob.glob(".ai/graphs/*.yaml"):
            with open(path) as f:
                g = yaml.safe_load(f)
            for t in g.get("transitions", []):
                assert "decided_by" in t, f"{path}: transition missing decided_by: {t}"
                assert t["decided_by"] in {"verifier", "policy", "human", "kernel"}, \
                    f"{path}: invalid decided_by: {t['decided_by']}"
    ```

### Acceptance criteria

- ✅ `pytest cli/tests/test_yaml_valid.py -v` → all pass
- ✅ Manually verify `verifier-rules.yaml` มี 4 layers (deterministic/policy/llm/human)
- ✅ `grep -c "decided_by:" .ai/graphs/*.yaml` ≥ 8 transitions per graph
- ✅ `loop-budget.yaml` มี `max_iterations`, `max_duration_minutes`, `max_tool_calls` ทั้ง 3

### Spec refs

- `02_VERIFIER_SPEC.md` (Pyramid)
- `03_GOAL_LOOP_SPEC.md` (Loop budget)
- `04_GRAPH_SPEC.md` (decided_by)

---

## Commit 3 — Port V2 Workflow (TRINITY_LEGACY uncommitted)

**Goal:** เอา v2 work ที่ยัง uncommitted ใน TRINITY_LEGACY/.ai/ เข้า trinity_v2

### Files affected (~12)

**New (untracked) — direct copy:**
- `cli/core/artifacts.py`, `kernel.py`, `session_naming.py`
- `cli/tests/test_session_naming.py`
- `docs/SESSION_NAMING.md`, `docs/V2_MIGRATION.md`
- `memory/KNOWN_ISSUES.md`, `memory/TRINITY_IMPROVEMENTS.md`
- `templates/session/SANDBOX/{00_BRAINSTORM,01_DEBATE,02_gemini,03_claude,04_codex}/` (full subtrees)

**Modified — overwrite:**
- `cli/commands/debate.py` (working tree version)
- `cli/commands/session.py` (working tree version)
- `templates/session/README.md` (working tree)

### Sub-tasks

13. Copy untracked files via `cp` from `TRINITY_LEGACY/.ai/` working tree
14. Overwrite modified files via `cp` from working tree (NOT git archive)
15. Copy numbered SANDBOX templates (5 directories)
16. Run `pytest cli/tests` — should still 14/14 + new `test_session_naming` cases pass
17. Test session creation: `bash .ai/cli/ai session new "fix: smoke test"` — verify output structure

### Acceptance criteria

- ✅ `pytest cli/tests` all pass (including test_session_naming)
- ✅ `bash .ai/cli/ai session new "fix: smoke"` creates session with: `THINK/`, `SANDBOX/00_BRAINSTORM/`, `SANDBOX/01_DEBATE/`, `SANDBOX/02_gemini/`, `SANDBOX/03_claude/`, `SANDBOX/04_codex/`, `DO/`, `CONTROL/`, `.state/`
- ✅ Session naming format ตรงกับ `docs/SESSION_NAMING.md`

---

## Commit 4 — Browser-CLI Contract References

**Goal:** ติด tool contract reference (docs only, mark non-active)

### Files affected (~7)

```
trinity_v2/docs/contracts/browser-cli/
├── README.md                   ← NEW — "REFERENCE ONLY" notice
├── COMMAND_CONTRACT.md         ← from browser-cli/docs/
├── RESPONSE_SCHEMA.md          ← from browser-cli/docs/
├── POLICY_TIERS.md             ← from browser-cli/docs/
├── ARCHITECTURE.md             ← from browser-cli/docs/
└── AI_AGENT_GUIDE.md           ← from browser-cli/docs/
trinity_v2/docs/schemas/browser-cli/
├── config.schema.json          ← from browser-cli/schema/
└── response-v2.schema.json     ← from browser-cli/schema/
```

### Sub-tasks

18. Create `docs/contracts/browser-cli/README.md` with notice:
    > ⚠️ **REFERENCE ONLY** — เอกสารในโฟลเดอร์นี้คือ DNA reference จาก `<workspace-root>/browser-cli/` ไม่ใช่ active code ของ trinity_v2. ใช้เป็นต้นแบบสำหรับ tool ใหม่ (memory-cli, verify-cli) ตาม `01_TOOL_CONTRACT.md`
19. Copy 5 markdown docs
20. Copy 2 JSON schemas

### Acceptance criteria

- ✅ ไฟล์ทั้ง 8 มีอยู่
- ✅ README.md มีคำว่า "REFERENCE ONLY"

### Spec refs

- `01_TOOL_CONTRACT.md` (Tool Contract spec)
- `11_RELATED_PROJECTS.md` (browser-cli as DNA reference)

---

## Commit 5 — Knowledge Brain (<upstream-project>/ai-docs scrubbed)

**Goal:** Copy 11 ไฟล์ + sanitize 3 ไฟล์ที่ contaminated

### Files affected (11)

Source: `<upstream-project>/ai-docs/0[1-4]-*/`

```
trinity_v2/ai-docs/
├── 01-CORE_PROTOCOL/
│   ├── GOD_TEAM_INTERACTION.md          ← copy as-is
│   ├── HUMAN_AGENT_INTERACTION.md       ← copy as-is
│   ├── MULTI_AI_COLLABORATION.md        ← copy as-is
│   ├── SAFETY_GATES.md                  ⚠️ SCRUB
│   ├── TOOL_USAGE.md                    ← copy as-is
│   └── WORKFLOW.md                      ← copy as-is
├── 02-STANDARDS/
│   ├── ENV_VARS.md                      ⚠️ SCRUB
│   ├── HUMAN_INTERFACE.md               ← copy as-is
│   ├── QUICK_REF.md                     ← copy as-is
│   └── UNIVERSAL_RULES.md               ← copy as-is
├── 03-PROCESS/
│   └── ROLLBACK_PROCEDURES.md           ⚠️ SCRUB
└── 04-MEMORY/
    └── (empty — placeholder for Phase 2 memory-cli)
```

### Scrub patterns (sed-style)

```bash
# In SAFETY_GATES.md, ENV_VARS.md, ROLLBACK_PROCEDURES.md:
s|<upstream-project>|{{PROJECT_NAME}}|g
s|smarty|{{TEMPLATE_ENGINE}}|g
s|deploy_dev_order_detail\.sh|{{DEPLOY_SCRIPT_DEV}}|g
s|deploy_prod_slip_verification\.sh|{{DEPLOY_SCRIPT_PROD}}|g
s|<workspace-root>/<upstream-project>|{{APP_DIR}}|g
s|FTP_CRED[A-Z_]*|{{FTP_CREDENTIALS_REF}}|g
# Plus manual review for any remaining <upstream-project>-specific references
```

### Sub-tasks

21. `cp -r <upstream-project>/ai-docs/0[1-4]-*/ trinity_v2/ai-docs/`
22. Apply scrub patterns to 3 contaminated files
23. Manual review of 3 scrubbed files (look for residual <upstream-project>-specific content)
24. Verify clean

### Acceptance criteria

- ✅ `find trinity_v2/ai-docs -type f -name "*.md" | wc -l` ≥ 11
- ✅ `grep -ril "<upstream-project>\|smarty\|deploy_dev_order\|deploy_prod_slip\|FTP_CRED" trinity_v2/ai-docs/` → 0 matches
- ✅ `grep -l "{{PROJECT_NAME}}\|{{APP_DIR}}\|{{TEMPLATE_ENGINE}}" trinity_v2/ai-docs/` shows the 3 scrubbed files

### Risk mitigation (per D6)

- ⚠️ Star/Gemini/Claude all flagged contamination risk
- ✅ User overrode with B = <upstream-project>/ai-docs/
- ✅ Scrub is strict + verified post-copy

---

## Commit 6 — Shim References (vendor-agnostic)

**Goal:** Copy <upstream-project> skills as reference + create canonical `.ai/shims/` skeleton (vendor-agnostic)

### Files affected

**Reference (copy as-is):**
```
trinity_v2/references/shims/upstream-skills/
├── lll/      ← from <upstream-project>/.claude/skills/lll/
├── vvv/      ← from <upstream-project>/.claude/skills/vvv/
├── nnn/      ← from <upstream-project>/.claude/skills/nnn/
├── gogogo/   ← from <upstream-project>/.claude/skills/gogogo/
└── rrr/      ← from <upstream-project>/.claude/skills/rrr/
```

**Canonical skeleton (NEW):**
```
trinity_v2/.ai/shims/
├── README.md                 ← explain Universal Shell + Adapter pattern
├── lll/SHIM.md               ← canonical spec (vendor-agnostic)
├── vvv/SHIM.md
├── nnn/SHIM.md
├── gogogo/SHIM.md
└── rrr/SHIM.md
```

### Sub-tasks

25. `cp -r <upstream-project>/.claude/skills/{lll,vvv,nnn,gogogo,rrr} trinity_v2/references/shims/upstream-skills/`
26. Create `trinity_v2/.ai/shims/README.md` explaining 2-layer pattern (Universal Shell + Vendor Adapter) per `07_SHIM_SPEC.md §4`
27. Create 5 stub SHIM.md files (one per short code) — each describes vendor-agnostic behavior, deferring vendor specifics to adapters

### Acceptance criteria

- ✅ `references/shims/upstream-skills/` has 5 directories
- ✅ `.ai/shims/` has README + 5 SHIM.md stubs
- ✅ `.ai/shims/README.md` references `07_SHIM_SPEC.md`
- ❌ **NO** `.claude/skills/` populated yet (Phase 8 task — vendor adapters generate from canonical)

### Spec refs

- `07_SHIM_SPEC.md §4` (Universal Shell + Vendor Adapter)
- D7 (Locked decision)

---

## Commit 7 — Brain Seed Sample + External References

**Goal:** Sample retros + chatgpt_specs + github_examples docs (as references, not for indexing)

### Files affected

```
trinity_v2/references/
├── brain-seed/
│   └── upstream-retros/        ← 10–20 representative retros, scrubbed
├── chatgpt_specs/            ← full copy from TRINITY_LEGACY/references/chatgpt_specs/ (368K)
└── github_examples/
    ├── claw-code/            ← *.md only (skip lock files / containerfile)
    ├── oh-my-claudecode/     ← *.md only
    ├── openclaude/           ← *.md only
    ├── thClaws/              ← *.md only
    ├── oh-my-codex/          ← *.md only
    ├── oh-my-openagent/      ← *.md only
    └── autoresearch/         ← *.md only
```

### Sub-tasks

28. **Sample retros:** Select 10-20 representative from `<upstream-project>/.claude/retrospectives/` (criteria: cover diverse topics, exclude any with `password|credential|secret|FTP_PASSWORD` after grep)
29. Scrub each sampled retro (apply same patterns as Commit 5)
30. Copy `chatgpt_specs/` whole (already clean)
31. Copy `github_examples/`:
    ```bash
    rsync -av --include="*/" --include="*.md" --include="*.json" \
          --exclude="node_modules" --exclude="dist" --exclude="target" \
          --exclude="*.lock" --exclude="Cargo.lock" --exclude="bun.lock" \
          --exclude="package-lock.json" --exclude=".git" \
          TRINITY_LEGACY/references/github_example/ trinity_v2/references/github_examples/
    ```

### Acceptance criteria

- ✅ `references/brain-seed/upstream-retros/*.md | wc -l` between 10 and 20
- ✅ `grep -ril "password\|credential\|FTP_PASSWORD" references/brain-seed/` → 0 matches
- ✅ `du -sh references/github_examples/` < 10MB
- ✅ `ls references/chatgpt_specs/` shows all original folders (00_master, 01_core, ..., optional)

---

## Final acceptance (after all 7 commits)

```bash
cd trinity_v2

# 1. Core runnable
bash .ai/cli/ai status                   # exit 0

# 2. Tests pass
cd .ai && python3 -m pytest cli/tests -q  # all pass

# 3. Session creation works
cd .. && bash .ai/cli/ai session new "fix: final smoke"  # creates full structure

# 4. No contamination
grep -ril "<upstream-project>\|smarty\|FTP_CRED" trinity_v2/ai-docs/ trinity_v2/.ai/  # 0 matches

# 5. No absolute paths in config
grep -r "<user-home>" trinity_v2/.ai/ssot.yaml trinity_v2/.ai/policies/  # 0 matches

# 6. Hash chain valid
python3 -c "import json,hashlib; e=json.loads(open('.ai/audit/events.ndjson').readline()); c=json.dumps({k:v for k,v in e.items() if k!='hash'},sort_keys=True,separators=(',',':')); assert e['hash']==hashlib.sha256(c.encode()).hexdigest()"

# 7. Git status
git status   # clean (all committed)
git log --oneline | wc -l   # 8 commits (init + 7)
```

If ALL pass → **trinity_v2 is Phase 0.5 complete and ready for Phase 1+ implementation work**

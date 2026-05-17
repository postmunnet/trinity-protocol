# AI-Native Workflow Protocol (v2.0)

> **Core Principle**: Verify (vvv) > Plan (nnn) > Execute (gogogo) > Reflect (rrr)

## 🔄 The Universal Loop


0.  **`ttt` (The Trinity Terminal) -- *The Dashboard Setup***
    *   **User asks**: "Start the engine." or `ttt`
    *   **Action**: Run `./scripts/ttt.sh` (or alias).
    *   **Setup**: The user manually splits the terminal into 3 panes (Cockpit View).
    *   **Execution**: Run the "God Mode" commands in each pane:
        *   **Pane 1 (Gemini)**: `gemini --yolo`
        *   **Pane 2 (Claude)**: `claude --dangerously-skip-permissions`
        *   **Pane 3 (Codex)**: `codex --full-auto`
    *   **Result**: 3 Interactive Agents ready for direct commands (`>`).

1.  **`lll` (Locate & Status) -- *Session Start Signal***
    *   **Binding contract**: [../protocols/LLL_CONTRACT.md](../protocols/LLL_CONTRACT.md) (v1.0, 2026-04-23)
    *   **Template**: [../templates/lll_output_v3.md](../templates/lll_output_v3.md) (v3.0)
    *   **Examples**: [../templates/lll_output_v3_examples.md](../templates/lll_output_v3_examples.md)
    *   **User asks**: "What is the status?" / "Where are we?" / พิมพ์ `lll`
    *   **Agent action**:
        *   🇹🇭 ตอบภาษาไทย 100% (hard rule)
        *   Fill 4 mandatory sections: Language / Identity / Carryover / Next Actions
        *   Pull Carryover §3 จาก last retro §29 §30 §31
        *   Conditional: §5 Onboarding + §6 Tools if new session
        *   Detect new vs repeat `lll` — repeat ย่อให้เหลือ Identity + Next Actions
    *   **Output**: Session Start Signal per template v3.0 (Thai, signal-first, carryover-aware)

2.  **`vvv` (Verify & Validate) -- *The Safety Gate***
    *   **Binding contract**: [../protocols/VVV_CONTRACT.md](../protocols/VVV_CONTRACT.md)
    *   **Template**: [../templates/vvv_report_v1.md](../templates/vvv_report_v1.md)
    *   **User asks**: "Fix the bug in X."
    *   **Agent action**:
        *   STOP. Do not edit yet.
        *   Produce VVV Report (9 sections, 5 mandatory)
        *   Echo interpretation in §1 (กัน misinterpret)
        *   Evidence rank 1-3 required in §3
        *   ASCII Art in §4 if flow/gate/layout/alignment/multi-entrypoint
        *   Scope §7 must list both in-scope AND out-of-scope
        *   Confidence §9 ≥ 80 + unknowns ≤ 2 → PROCEED_TO_NNN
    *   **Output**: VVV Report per template v1.0 (see examples `../templates/vvv_report_v1_examples.md`)

3.  **`nnn` (Navigate & Plan)**
    *   **Binding contract**: [../protocols/NNN_CONTRACT.md](../protocols/NNN_CONTRACT.md) (v1.0, 2026-04-23)
    *   **Template**: [../templates/nnn_plan_v1.md](../templates/nnn_plan_v1.md)
    *   **Examples**: [../templates/nnn_plan_v1_examples.md](../templates/nnn_plan_v1_examples.md)
    *   **Inheritance**: MUST inherit from preceding `vvv` (§6 Verified Target + §7 Scope)
    *   **User asks**: "Go ahead." / พิมพ์ `nnn` หลัง vvv
    *   **Agent action**:
        *   Cite vvv + echo §6 + §7 in §1 Plan Goal
        *   Break into tasks with: name + files (w/ lines) + action + est (minutes) + deps
        *   Specify order (sequential/parallel) + critical path
        *   State total estimate + risk + complexity
        *   If total > 2h → break into phases
        *   Conditional: §6 Diagram, §7 Rollback, §8 Test Plan, §9 Breaking Changes
        *   ⏸️ **Wait for `gogogo`** — never auto-proceed
    *   **Output**: Implementation Plan per template v1.0 — respects vvv §7 (no scope creep)

4.  **`gogogo` (Execute) -- *Deploy Rituals Enforced***
    *   **Binding contract**: [../protocols/GOGOGO_CONTRACT.md](../protocols/GOGOGO_CONTRACT.md) (v1.0, 2026-04-23)
    *   **Template**: [../templates/gogogo_execute_v1.md](../templates/gogogo_execute_v1.md)
    *   **Examples**: [../templates/gogogo_execute_v1_examples.md](../templates/gogogo_execute_v1_examples.md)
    *   **Inheritance**: requires approved `nnn` (§5 Approval Gate confirmed)
    *   **User asks**: "Do it." / `gogogo` / "A จัดมา" / short directives
    *   **Agent action**:
        *   Execute tasks in nnn §3 order — track status + duration per task
        *   `php -l` / {{TEMPLATE_ENGINE}} / MySQL syntax check per file
        *   `trinity_deploy.sh dev` → **MD5 pull-back** (required)
        *   ⏸️ **WAIT** for user `promote prod` — never auto-proceed
        *   `trinity_deploy.sh prod` → MD5 + marker grep verify
        *   Cache-bust if TPL/JS/CSS + CF involved
        *   "Deploy Successful" ≠ verified — MD5 is truth
    *   **Output**: Execution report per template v1.0 (MD5 tables, rollback log if triggered)

5.  **`rrr` (Review & Retrospective)**
    *   **Binding contract**: [../protocols/RRR_CONTRACT.md](../protocols/RRR_CONTRACT.md)
    *   **Template**: [../templates/retrospective_v3.md](../templates/retrospective_v3.md) (v3.0, 33 sections)
    *   **Example**: [../templates/retrospective_v3_example.md](../templates/retrospective_v3_example.md)
    *   **User asks**: "It works." / "ขอบคุณ" / "เสร็จแล้ว"
    *   **Agent action**:
        *   Produce Retrospective following Template v3 (25 mandatory + 8 conditional sections)
        *   Fill §18 Workflow Compliance + §19 Safety Gates audit
        *   Include §23 Honest Feedback (must have self-critique, not "all went well")
        *   Every lesson in §15 must have Anti-application field
        *   Every decision in §10 must have rejected alternatives
        *   Propose memory updates (§26) — ask user to confirm save
    *   **Output**: `.claude/retrospectives/YYYY-MM/{seq:04d}_{date}_{hour}_{minute}_{ampm}_{type}-{slug}.md` (Trinity-aligned — see [SESSION_NAMING.md](../../../TRINITY_LEGACY/.ai/docs/SESSION_NAMING.md))

---

## 🛠️ Tool Usage Guide

### CLI Tools
*   `grep -rn "pattern" .`: Use to finding code.
*   `ls -R`: Use to verify file existence.
*   `cat`: Use to read file content (limit to small files).

### Agent Modes
*   **Claude (`--introspect`)**: Use when stuck or need deep reasoning.
*   **Gemini (`--analyze`)**: Use for architectural review.
*   **Codex (`/codex-generate`)**: Use for pure code generation.

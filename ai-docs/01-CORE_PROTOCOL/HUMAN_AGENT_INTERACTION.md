# 🧠 Human-Agent Interaction Protocol (Master Protocol v2.0)

> **Core Philosophy**: Humans Direct, AI Executes, Everyone Verifies.
> **Status**: Active | **Version**: 2.0

---

## 1. The Interaction Model

We use a **Commander-Unit** model:
*   **Human (Commander)**: Sets goals (`PLAN.md`), triggers workflows (`ttt`), and reviews outcomes (`rrr`).
*   **AI Swarm (Units)**: Executes tasks in parallel, reports status, and requests decisions.

### The Feedback Loop
The collaboration is not a straight line, but a continuous loop:
1.  **Command** (Human) → 2. **Plan** (Gemini) → 3. **Verify** (Claude) → 4. **Build** (Codex) → 5. **Report** (Shared) → 1. **Review** (Human)

---

## 2. The `ttt` Trigger Protocol

Most sessions start with the `ttt` (Team Start) command. This is not just "starting apps"; it's initializing the **Swarm Intelligence**.

### Protocol Steps:
1.  **Human Action**: User types `ttt`.
2.  **Orchestrator Action**:
    *   Kills stale processes (`kill -9 ...`).
    *   Spawns agents in background (`gemini`, `claude`, `codex`).
    *   Redirects logs to `.ai/logs/`.
3.  **Verification**: Orchestrator confirms "Agents Started".

**Why this matters**: It ensures a "Clean Slate" state every time. No lingering variables or zombie processes.

---

## 3. The Injection & Capture Mechanism

When the Human (or Orchestrator) talks to a specific agent, we follow the **Injection Protocol**:

### Phase 1: Injection 💉
Passing a prompt to a running agent.
*   **Method**: `send_command_input`
*   **Standard**: Must include a `WaitMs` to allow processing.
*   **Safety**: Ensure the target CommandID matches the active PID.

### Phase 2: Capture 👁️
Reading the agent's response.
*   **Primary Capture**: Read immediate output.
*   **The "Poke" Technique**: If output is empty/stalled, inject an empty `\n` to refresh the terminal buffer.

### Phase 3: Synthesis 📝
Merging outputs from multiple agents into a single report (`WORK_PLAN.md` or Chat Response).

---

## 4. Workspaces & Isolation

Humans and Agents have distinct territories:

| Zone | Path | Who Writes? |
|------|------|-------------|
| **Development** | `deploy_dev_*/` | **Codex**, **Human** |
| **Production** | `deploy_prod_*/` | **Nobody** (Copy only) |
| **Status/Docs** | `ai-docs/SYSTEM_STATUS.md` | **Gemini**, **Human** |
| **Logic/Plans** | `.ai/sessions/.../PLAN.md` | **Gemini**, **Human** |
| **Logs** | `.ai/logs/` | **System** (Auto) |

**Rule**: Agents must never touch files outside their designated workspace references without specific instructions.

---

## 5. Human Commands (Short Codes)

The Human controls the tempo using standardized short codes:

*   **`lll`**: "I need situational awareness." (Report status)
*   **`vvv`**: "I doubt this. Verify it." (Run tests/checks)
*   **`nnn`**: "I agree. Make a plan." (Create implementation detail)
*   **`gogogo`**: "Execute the plan." (Write code)
*   **`rrr`**: "Let's reflect." (Update status and lessons)

---

## 6. Critical Safety: The "Halt" Protocol

If an Agent detects a dangerous pattern (e.g., hardcoded credentials, production path edit):
1.  **STOP** immediately.
2.  **REPORT** to Human.
3.  **WAIT** for explicit override.

**Human Override**: Must provide a reason (e.g., "Authorized hotfix for incident related to X").

---

*Version 2.0 - Optimized for CLI-based Agent Swarms*

---
title: "Quick Reference: Fluid Leadership Protocol"
category: standards
read-time: 5min
frequency: frequent
priority: high
tags: [workflow, commands, fluid-leadership, cheatsheet]
last-updated: 2025-12-19
---

# Quick Reference: Fluid Leadership Protocol

This document provides a quick, scannable reference for using the Fluid Leadership workflow with the AI Team (Gemini, Claude, Codex).

---

## 1. Quick Reference Card (การ์ดอ้างอิงฉบับย่อ)

### Core Commands

| Command | Description | Target |
| :--- | :--- | :--- |
| **`ttt`** | **Team, Assemble**: Starts all agents (Gemini, Claude, Codex) in the background. The first command of any session. | System |
| **`lead <agent>`** | **Set Leader**: Assigns leadership to a specific agent (`gemini`, `claude`, or `codex`). Mandatory after `ttt`. | System |
| **`handoff <agent>`** | **Handoff Leadership**: Formally passes leadership and context to a new agent. | System |
| **`lll`** | **Leader, Status?**: Asks the current Lead Agent for a status update. | Lead Agent |
| **`vvv`** | **Leader, Verify**: Delegates a verification task to the current Lead Agent. | Lead Agent |
| **`nnn`** | **Leader, Plan**: Asks the current Lead Agent to create a plan. | Lead Agent |
| **`gogogo`** | **Leader, Execute**: Tells the current Lead Agent to execute the approved plan. | Lead Agent |
| **`rrr`** | **Leader, Record**: Asks the current Lead Agent to create a retrospective summary. | Lead Agent |

### Leadership Selection Matrix

Use this matrix to decide which agent should lead which phase of a task.

| Task Phase | Description | Recommended Lead Agent | Rationale |
| :--- | :--- | :--- | :--- |
| **Discovery & Planning** | Researching new concepts, analyzing requirements, defining architecture, creating high-level plans. | **Gemini** (Architect) | Best for system design, coordination, and synthesizing large amounts of information. |
| **Implementation & Automation** | Writing code, creating scripts, implementing technical details, building the solution. | **Codex** (Builder) | Best for technical execution, automation, and code correctness. |
| **Review & Safety** | Reviewing code for security, checking for risks, analyzing compliance, ensuring quality. | **Claude** (Safety Officer) | Best for deep analysis, risk assessment, and ensuring process compliance. |

---

## 2. Visual Workflow Diagram (แผนภาพ Workflow)

This diagram illustrates the flow of a typical task using the Fluid Leadership model.

```ascii
               +------------------+
               |  HUMAN OPERATOR  |
               +------------------+
                     |
 Anfang & Ende: ttt    |
                     V
+-----------------------------------------------------------------+
|                        LEADERSHIP FLOW                          |
|                                                                 |
|  [1. RESEARCH PHASE]        [2. BUILD PHASE]                    |
|   `lead gemini`              `lead codex`                       |
| +--------------+   handoff   +-------------+                    |
| |    GEMINI    | ----------> |    CODEX    |                    |
| | (Architect)  |             |  (Builder)  |                    |
| +--------------+             +-------------+                    |
|   ^     |                      |                                |
|   |     | handoff              | handoff                        |
|   |     V                      V                                |
|   +--------------+   <--------+                                |
|   |    CLAUDE    |                                              |
|   | (Safety Off.)|                                              |
|   +--------------+                                              |
|   `lead claude`                                                 |
|  [3. REVIEW PHASE]                                              |
|                                                                 |
+-----------------------------------------------------------------+
```

**Flow Description:**
1.  **Research**: The user starts by setting **Gemini** as the leader to research and plan the task.
2.  **Build**: Once a plan is approved, leadership is handed off to **Codex** to build the solution.
3.  **Review**: After the build is complete, leadership is handed off to **Claude** to perform a safety and quality review before finalizing the task.

---

## 3. Error Recovery Examples (ตัวอย่างการกู้คืนระบบ)

### Scenario 1: Lead Agent Crashes or Becomes Unresponsive

**Problem**: You issue a command like `lll`, but the Lead Agent does not respond or returns an error.

**Recovery Steps**:
1.  **Confirm the Crash**: Check the agent's log file for errors (e.g., `ai-docs/runtime/logs/gemini.log`).
2.  **Re-Assemble the Team**: Run the `ttt` command again. This is designed to safely kill any old, broken processes and start a fresh team.
    ```bash
    > ttt
    System: Team assembled. Set the initial leader with `lead <agent>`.
    ```
3.  **Re-Establish Leadership**: Set the leader again for the current phase.
    ```bash
    > lead gemini
    System: Gemini is now leading.
    ```
4.  **Retry**: Re-issue your last command (e.g., `lll`). The fresh agent should now be able to handle it.

### Scenario 2: Handoff Refusal

**Problem**: You try to pass leadership with `handoff codex`, but the system returns a message like `ERROR: Codex cannot take leadership. Reason: Currently processing a build task.`

**Recovery Steps**:
1.  **Acknowledge the Blocker**: Do not force the handoff. The agent has a valid reason for refusal.
2.  **Query the Target Agent's Status**: Ask the current leader to check on the busy agent.
    ```bash
    > lll --agent=codex
    Lead Agent (Gemini): Codex reports it is 75% complete with the 'gogogo' build task. ETA: 5 minutes.
    ```
3.  **Wait or Re-plan**:
    *   **Option A (Wait)**: Wait for the estimated time and try the `handoff` command again.
    *   **Option B (Re-plan)**: If the task is urgent, decide if another agent can take over or if the current work needs to be cancelled.

### Scenario 3: `ttt` Startup Failure

**Problem**: You run `ttt` and the system reports a failure: `ERROR: Team assembly failed. Agent 'claude' did not start.`

**Recovery Steps**:
1.  **Isolate the Problem**: The system has told you the specific agent that failed. The issue is with `claude`.
2.  **Check the Logs**: This is the most critical step. Open the log file for the failed agent to find the root cause.
    ```bash
    > cat ai-docs/runtime/logs/claude.log
    ```
3.  **Debug the Issue**: The log will contain the error message. Common causes include:
    *   `API key not found or invalid`: Check your environment variables or secret management.
    *   `Command not found`: The agent's CLI tool might not be installed correctly or is not in the system's PATH.
    *   `Configuration error`: There might be a syntax error in `ai-docs/config/agents.json`.
4.  **Fix and Retry**: After fixing the underlying issue (e.g., setting the correct API key), run `ttt` again.

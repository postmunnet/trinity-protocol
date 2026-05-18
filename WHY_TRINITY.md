# Why Trinity?

Language: English | [ไทย](WHY_TRINITY_TH.md)

AI coding agents are powerful, but their claims are not reliable evidence.

They can say "done" without proving that the work is done.

They may say:

- tests pass, but no test artifact exists
- a bug is fixed, but no reproduction was verified
- a deploy is safe, but no rollback path was recorded
- a file was changed correctly, but no diff was inspected

Trinity exists to make AI-assisted work evidence-driven.

---

## Before Trinity

```text
User: Fix the login bug.
Agent: Done. Tests pass.
```

The problem is not that the agent is always wrong.

The problem is that the claim is not enough.

There is no trustworthy proof:

- no scoped plan
- no diff summary
- no test log
- no verifier verdict
- no audit event
- no promotion decision

---

## After Trinity

```text
User: Fix the login bug.
Trinity:
1. Requires a scoped plan artifact
2. Allows execution only within approved boundaries
3. Captures diffs, logs, test output, screenshots, or other evidence
4. Runs verifier rules against the evidence
5. Allows promotion only after the evidence passes
```

If there is no artifact, there is no trust.

If verification does not pass, the work is not complete.

If no authorized layer approves the transition, the work cannot move forward.

---

## Core Principle

```text
Trust artifacts, not claims.
```

An AI agent can propose. It can execute within scope. It can write artifacts.

But it should not be the final authority that decides its own work is complete.

Trinity uses a simple judgment order:

```text
Deterministic verifier
    -> Policy / rules
    -> LLM judge only when gated
    -> Human authority
```

---

## What Trinity Is

Trinity is a CLI-first control layer for AI coding agents.

It coordinates vendor AI harnesses, verifies their work, and records decisions
as auditable artifacts.

It is designed for developers and technical operators who already use tools
like Claude Code, Codex, Cursor, or Gemini, but do not want to trust agent
claims without evidence.

---

## What Trinity Is Not

Trinity is not:

- another chatbot
- another general agent framework
- an MCP-first tool registry
- a memory app
- a generic orchestrator
- a replacement for vendor AI harnesses

Trinity is the control plane between human intent and AI execution.

---

## The Short Version

Trinity does not make AI smarter.

Trinity makes AI work accountable.

```text
No artifact = no trust.
No verification = no completion.
No authority = no transition.
```

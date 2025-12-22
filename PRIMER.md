# Trinity Protocol PRIMER

**Version:** v0.5 / Phase 6.1 (Agent Sandbox Enabled)
**Last Updated:** 2025-12-21

Purpose: Onboard quickly and safely to the Trinity Protocol.

---

## Quick Start (2 min)

**What:** Trinity moves from chat to artifacts with 3 Locks + Agent Sandboxes.

**Where:** Control plane in `.ai/`, work in sessions under `.ai/sessions/`.

**How (v0.5):**
```bash
ai session new "Task Name"        # Create session with SANDBOX/
ai snapshot                       # Backup current state
# Agents work in SANDBOX/gemini|claude|codex/
ai debate compile --mode fast     # Compile proposals (optional)
ai debate publish                 # Publish verdict to CONSENSUS.md (optional)
ai sandbox apply codex            # Apply patch.diff to DO/dev
ai verify dev                     # Verify changes
ai promote                        # Move to DO/prod (requires CONSENSUS.md)
ai verify prod                    # Verify production
ai close                          # Close session (requires verify_prod PASS)
ai sandbox clean                  # Archive/remove SANDBOX (optional)
ai unlock                         # Force-break stale lock if needed
```

---

## Trust Boundaries (v0.5)

**Human-Only Write:**
- `.ai/policies/**` (governance)
- `.ai/PRIMER.md`, `.ai/SESSION_CONTRACT.md` (specs)
- `sessions/*/THINK/**` (planning)
- `sessions/*/SANDBOX/DEBATE/verdict.md` (decision)

**Agent-Write (Sandboxed):**
- `SANDBOX/gemini/**` (Gemini only)
- `SANDBOX/claude/**` (Claude only)
- `SANDBOX/codex/**` (Codex only)

**System-Only Write:**
- `.ai/.state/**` (global state)
- `sessions/*/.state/**` (session state)
- `sessions/*/CONTROL/**` (metadata)
- `sessions/*/DO/snapshot/**` (immutable backup)
- `sessions/*/DO/prod/**` (via `ai promote` only)
- `sessions/*/SANDBOX/DEBATE/**` (via `ai debate compile`)

---

## Session Structure (v0.5 - Hybrid Model)

```
sessions/YYYY-MM-DD_task/
├── THINK/           # Human planning
├── SANDBOX/         # 🆕 Agent workspaces (disposable)
│   ├── gemini/      # Research & analysis
│   ├── claude/      # Planning & safety
│   ├── codex/       # Implementation
│   └── DEBATE/      # Compiled debate artifacts
├── DO/              # Execution (deploy-ready)
│   ├── snapshot/    # Immutable backup
│   ├── dev/         # Single ingress via patch.diff
│   └── prod/        # Via ai promote only
├── CONTROL/         # Status & metadata
└── .state/          # 🆕 Session-local state (system-only)
```

---

## Key Concepts (v0.5)

**Agent Sandboxes:** Isolated workspaces for parallel agent work.

**Single Ingress:** Only `ai sandbox apply` writes to `DO/dev/` (via patch.diff).

**Debate Workflow:** Agents propose → Human decides → Publish consensus.

**Session-Local State:** Each session tracks its own state (crash-resumable).

---

## Start Here

**First Time:**
1. Read `SESSION_CONTRACT.md` (5 min) - Canonical spec
2. Create session: `ai session new "Your Task"`
3. Follow workflow above

**For Details:**
- Session structure: `SESSION_CONTRACT.md`
- Architecture: `MASTER_BLUEPRINT.md`
- Commands: `docs/USER_MANUAL.md` (if exists)

---

**🌌 Trinity v0.5 - Infrastructure for Multi-Agent Development**

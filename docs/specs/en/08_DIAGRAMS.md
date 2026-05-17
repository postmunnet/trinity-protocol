---
title: "Trinity OS — Visual Diagrams (English)"
subtitle: "Mermaid diagrams + ASCII for architecture, flows, state machines"
language: English
version: 1.0.0
status: reference
last-updated: 2026-04-28
note: "Translation of ../08_DIAGRAMS.md"
---

# Trinity OS Visual Diagrams (English)

> Mermaid + ASCII diagrams in one file — embed in docs, present to teams, brainstorm.

---

## 1. Trinity OS — Full Stack

### 1.1 Layered Architecture

```mermaid
graph TB
    User([👤 User / Goal])
    
    subgraph Vendor["🪞 VENDOR HARNESS — Reasoning Engine"]
        Claude[Claude Code]
        Codex[Codex CLI]
        Cursor[Cursor]
        Gemini[Gemini CLI]
    end
    
    subgraph Shim["🔌 TRINITY SHIM — Adapter"]
        Skills[".claude/skills"]
        AgentsMD["AGENTS.md"]
        CursorRules[".cursor/rules"]
        GeminiMD["GEMINI.md"]
        UnivShell[trinity-shell]
    end
    
    subgraph Kernel["⚙️ TRINITY KERNEL — Coordinator + Judge"]
        Loop[Loop]
        Graph[Graph]
        Policy[Policy]
        Audit[Audit]
        State[State]
    end
    
    subgraph Brain["🧠 KNOWLEDGE BRAIN"]
        AIDocs[ai-docs]
        Memory[memory-cli]
        Retros[retros]
        Lessons[lessons]
    end
    
    subgraph Tools["🛠 CLI TOOL USERLAND — Organs"]
        BrowserCLI[browser-cli]
        VerifyCLI[verify-cli]
        RetroCLI[retro-cli]
        FTPCLI[ftp-cli<br/>FTP/SFTP future]
        Future[future tools...]
    end
    
    User --> Vendor
    Vendor --> Shim
    Shim --> Kernel
    Kernel --> Brain
    Kernel --> Tools
    Brain -.context.-> Vendor
    Tools -.evidence.-> Kernel
```

### 1.2 ASCII Version

```text
┌──────────────────────────────────────────────────┐
│ 👤 USER / GOAL                                   │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 🪞 VENDOR HARNESS (Reasoning Engine)             │
│ Claude Code · Codex CLI · Cursor · Gemini · Warp │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ 🔌 TRINITY SHIM                                  │
│ • .claude/skills · AGENTS.md · .cursor/rules     │
│ • trinity-shell (universal CLI bridge)           │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ ⚙️  TRINITY KERNEL (Coordinator + Judge)         │
│ • Sessions · Loop · Graph · Policy · Audit       │
│ • events.ndjson (hash-chain)                     │
└──────────┬────────────────────────┬──────────────┘
           ▼                        ▼
┌──────────────────────┐  ┌─────────────────────────┐
│ 🧠 KNOWLEDGE BRAIN   │  │ 🛠 CLI TOOL USERLAND   │
│ ai-docs/             │  │ • browser-cli           │
│  ├── retros (240)    │  │ • memory-cli            │
│  ├── lessons (14)    │  │ • verify-cli            │
│  └── workflow ritual │  │ • retro-cli             │
│ memory-cli (search)  │  │ • wordpress-cli (future)│
└──────────────────────┘  │ • ftp-cli (future)      │
                          │ • deploy-cli (future)   │
                          └─────────────────────────┘
```

---

## 2. Iron Triangle — Harness + Loop + Graph

```mermaid
graph LR
    H[🪞 HARNESS<br/>Interface/Host<br/>vendor + shim]
    L[🔄 LOOP<br/>Goal-directed<br/>execution heart]
    G[🕸 GRAPH<br/>Workflow<br/>state machine]
    
    H -->|drives| L
    L -->|traverses| G
    G -->|gates| L
    L -->|reports| H
    
    H -.serves.-> User([👤 User])
    G -.uses.-> Verifier([⚖️ Verifier])
    L -.consults.-> Memory([🧠 Memory])
```

```text
       Harness
       (Interface)
           ↑
           │ user input
           │ user output
           │
           ▼
        ┌──────────────────────┐
        │     LOOP             │
        │  (heart - run cycle) │
        └────┬─────────────────┘
             │
     ┌───────┴────────┐
     │ traverse       │ verify
     ▼                ▼
   ┌──────┐      ┌─────────┐
   │GRAPH │ ←──→ │VERIFIER │
   │      │ gate │ (Judge) │
   └──────┘      └─────────┘
```

---

## 3. Pyramid of Judgment

```mermaid
graph TB
    H[👤 Human<br/>Final Authority]
    L[🤖 LLM Judge<br/>gated, audited]
    P[📋 Policy Rules<br/>.ai/policies/*.yaml]
    V[⚖️ Verifier<br/>verifier-rules.yaml<br/>deterministic]
    
    V -->|unsure| P
    P -->|unsure| L
    L -->|unsure| H
    
    style V fill:#90EE90
    style P fill:#FFD700
    style L fill:#FFA500
    style H fill:#FF6B6B
```

```text
         ┌─────────────┐
         │    Human    │  ← last resort
         └──────▲──────┘
                │ unsure
         ┌──────┴──────┐
         │  LLM Judge  │  ← gated, audited
         │  (gated)    │
         └──────▲──────┘
                │ unsure
         ┌──────┴──────┐
         │   Policy    │  ← .ai/policies/*.yaml
         │   Rules     │
         └──────▲──────┘
                │ unsure
         ┌──────┴──────┐
         │  Verifier   │  ← verifier-rules.yaml
         │ (deterministic)│
         └─────────────┘
```

---

## 4. Standard Workflow Graph

```mermaid
stateDiagram-v2
    [*] --> THINK
    THINK --> SANDBOX: plan_approved (human)
    THINK --> ESCALATED: plan_rejected (human)
    SANDBOX --> DO: vvv_pass (verifier)
    SANDBOX --> THINK: vvv_fail_retry (verifier)
    SANDBOX --> ESCALATED: vvv_needs_human (verifier)
    DO --> VERIFIED: code_change_pass (verifier)
    DO --> SANDBOX: code_change_retry (verifier)
    DO --> FAILED: code_change_dead (verifier)
    VERIFIED --> PROMOTED: promote_request (human)
    PROMOTED --> DEPLOYED: deploy_request (human)
    DEPLOYED --> PROMOTED: deploy_rollback (verifier)
    DEPLOYED --> RETRO: deploy_check_pass (verifier)
    DEPLOYED --> FAILED: deploy_check_dead (verifier)
    RETRO --> DONE: rrr_complete (kernel)
    DONE --> [*]
    FAILED --> [*]
    ESCALATED --> [*]
```

### 4.1 Authority Color Coding

```text
🟢 verifier  → most automated (PASS/RETRY/DEAD)
🟡 policy    → safety/budget enforcement
🔴 human     → sensitive (promote/deploy/destructive)
🔵 kernel    → mechanical (entry/exit, retry)
```

---

## 5. Goal Tree Example

```mermaid
graph TB
    Root[g_001 epic<br/>'Do SEO across whole site'<br/>running]
    
    F1[g_002 feature<br/>'Audit current state'<br/>done]
    F2[g_006 feature<br/>'Fix missing metadata'<br/>running]
    F3[g_009 feature<br/>'Verify + deploy'<br/>pending]
    
    T1[g_003 task<br/>'Crawl sitemap'<br/>done]
    T2[g_004 task<br/>'Extract metadata'<br/>done]
    T3[g_005 task<br/>'Generate report'<br/>done]
    T4[g_007 task<br/>'Pages 1-25'<br/>running]
    T5[g_008 task<br/>'Pages 26-50'<br/>pending]
    T6[g_010 task<br/>'Run tests'<br/>pending]
    T7[g_011 task<br/>'Deploy + monitor'<br/>pending]
    
    Root --> F1
    Root --> F2
    Root --> F3
    F1 --> T1
    F1 --> T2
    F1 --> T3
    F2 --> T4
    F2 --> T5
    F3 --> T6
    F3 --> T7
    
    style F1 fill:#90EE90
    style T1 fill:#90EE90
    style T2 fill:#90EE90
    style T3 fill:#90EE90
    style F2 fill:#FFD700
    style T4 fill:#FFD700
    style T5 fill:#E0E0E0
    style F3 fill:#E0E0E0
    style T6 fill:#E0E0E0
    style T7 fill:#E0E0E0
```

---

## 6. Loop Algorithm Flow

```mermaid
flowchart TD
    Start([Start: trinity loop --goal])
    Init[Initialize goal_tree<br/>+ loop_state]
    Budget{Budget<br/>OK?}
    Next{Next<br/>pending<br/>goal?}
    AllDone{All<br/>done?}
    Deadlock{Has<br/>blocked?}
    Execute[Execute goal<br/>via tools/AI]
    Verify[Call verify-cli]
    Verdict{Verdict?}
    MarkDone[Mark done<br/>checkpoint]
    Retry[Increment failure<br/>requeue]
    AskHuman[Pause<br/>ask user]
    MarkDead[Mark dead]
    Decompose{Was epic<br/>or feature?}
    DecomposeAct[Decompose<br/>enqueue subgoals]
    Persist[Persist state]
    Terminate([Terminate])
    
    Start --> Init
    Init --> Budget
    Budget -->|No| Terminate
    Budget -->|Yes| Next
    Next -->|None| AllDone
    AllDone -->|Yes| Terminate
    AllDone -->|No| Deadlock
    Deadlock -->|Yes| Terminate
    Deadlock -->|No| Next
    Next -->|Yes| Execute
    Execute --> Verify
    Verify --> Verdict
    Verdict -->|PASS| MarkDone
    Verdict -->|RETRY| Retry
    Verdict -->|NEEDS_HUMAN| AskHuman
    Verdict -->|DEAD| MarkDead
    MarkDone --> Decompose
    Decompose -->|Yes| DecomposeAct
    Decompose -->|No| Persist
    DecomposeAct --> Persist
    Retry --> Persist
    AskHuman --> Persist
    MarkDead --> Persist
    Persist --> Budget
```

---

## 7. Tool Contract — Common Envelope

```mermaid
graph LR
    subgraph Envelope["Response Envelope (NDJSON line)"]
        OK[ok: bool]
        Cmd[command: string]
        Action[action: 'tool.verb']
        Data[data: object|null]
        Artifacts[artifacts: array]
        Error[error: object|null]
        Meta[meta: object]
    end
    
    Meta --> Tool[tool: string]
    Meta --> SchemaV[schema_version]
    Meta --> RunID[run_id]
    Meta --> Duration[duration_ms]
    Meta --> Timestamp[timestamp]
```

```text
{
  "ok": true,                    ← MUST
  "command": "search",            ← MUST (local verb)
  "action": "memory.search",      ← MUST v1.1+ (canonical)
  "data": { ... },                ← MUST (tool-specific)
  "artifacts": [ ... ],           ← MUST (truth links)
  "error": null,                  ← MUST (null on success)
  "meta": {                       ← MUST
    "tool": "memory-cli@0.1.0",   ← MUST
    "schema_version": "1",        ← MUST
    "run_id": "run_xyz",          ← MUST
    "duration_ms": 42,            ← MUST
    "timestamp": "2026-04-28T..."  ← MUST
  }
}
```

---

## 8. Bootstrap Pack — Install Flow

```mermaid
sequenceDiagram
    participant User
    participant Install as install.sh
    participant FS as Filesystem
    participant Verify as verify-install.sh
    participant AI as AI Tool
    
    User->>Install: bash install.sh ./my-project
    Install->>User: prompt: project name?
    User->>Install: my-project
    Install->>User: prompt: tech stack?
    User->>Install: PHP+MySQL
    Install->>FS: mkdir .ai/ ai-docs/
    Install->>FS: render CLAUDE.md.template
    Install->>FS: render AGENTS.md.template
    Install->>FS: render GEMINI.md.template
    Install->>FS: ln -s WARP.md → CLAUDE.md
    Install->>FS: copy minimal ai-docs/
    Install->>FS: copy minimal .ai/
    Install->>User: ✅ Done
    
    User->>Verify: bash verify-install.sh
    Verify->>FS: check files exist
    Verify->>FS: check inline short codes
    Verify->>User: ✓ All checks pass
    
    User->>AI: Open Claude Code
    AI->>FS: Read CLAUDE.md
    User->>AI: lll
    AI->>User: Project status (knows short codes!)
```

---

## 9. Verify-cli — Verdict Decision Tree

```mermaid
flowchart TD
    Start([Verify request])
    Load[Load rule set<br/>verifier-rules.yaml]
    Evidence{All<br/>required<br/>evidence?}
    Checks{Run all<br/>checks}
    PassChk{Pass<br/>conditions<br/>met?}
    RetryChk{Retry<br/>conditions<br/>met?}
    HumanChk{Human<br/>conditions<br/>met?}
    DeadChk{Dead<br/>conditions<br/>met?}
    Pyramid{Escalate<br/>to policy?}
    
    PASS([PASS])
    RETRY([RETRY])
    NEEDS_HUMAN([NEEDS_HUMAN])
    DEAD([DEAD])
    
    Start --> Load
    Load --> Evidence
    Evidence -->|No| RETRY
    Evidence -->|Yes| Checks
    Checks --> PassChk
    PassChk -->|Yes| PASS
    PassChk -->|No| RetryChk
    RetryChk -->|Yes| RETRY
    RetryChk -->|No| HumanChk
    HumanChk -->|Yes| NEEDS_HUMAN
    HumanChk -->|No| DeadChk
    DeadChk -->|Yes| DEAD
    DeadChk -->|No| Pyramid
    Pyramid -->|Yes| NEEDS_HUMAN
    Pyramid -->|No| RETRY
    
    style PASS fill:#90EE90
    style RETRY fill:#FFD700
    style NEEDS_HUMAN fill:#FFA500
    style DEAD fill:#FF6B6B
```

---

## 10. Memory-cli Architecture

```mermaid
graph TB
    CLI[memory-cli<br/>stdin/stdout JSON]
    
    subgraph Indexer["Indexer"]
        Walk[Walk directory]
        Parse[Parse markdown<br/>+ frontmatter]
        Hash[Compute sha256]
        Insert[Insert to DB]
    end
    
    subgraph DB["SQLite DB (.memory/memory.db)"]
        Docs[(documents)]
        FTS[(documents_fts<br/>FTS5)]
        Tags[(tags)]
        Sup[(supersession)]
        Ev[(evidence_links)]
    end
    
    subgraph Sources["Source Markdown"]
        Retros[.claude/retrospectives/<br/>240 files]
        Lessons[ai-docs/real_lessons/<br/>14 files]
        Summaries[.ai/sessions/*/<br/>99_SUMMARY.md]
    end
    
    Sources --> Walk
    Walk --> Parse
    Parse --> Hash
    Hash --> Insert
    Insert --> Docs
    Insert --> FTS
    Insert --> Tags
    
    CLI --> Indexer
    CLI --> DB
    
    Docs <--> FTS
```

---

## 11. Tool Ecosystem — Vendor + Trinity Tools

```mermaid
graph LR
    User([User])
    
    subgraph VendorTools["Vendor Built-in (used as-is)"]
        Read[Read]
        Write[Write]
        Edit[Edit]
        Bash[Bash]
        Glob[Glob]
        Grep[Grep]
    end
    
    subgraph TrinityTools["Trinity CLI Tools (custom)"]
        Browser[browser-cli<br/>Playwright wrapper]
        Memory[memory-cli<br/>FTS5 + future vector]
        Retro[retro-cli<br/>structured writer]
        Verify[verify-cli<br/>Judge with rules]
        WP[wordpress-cli<br/>wp-cli wrapper]
        FTP[ftp-cli<br/>FTP/SFTP future]
        Deploy[deploy-cli<br/>future]
    end
    
    User --> VendorTools
    User --> TrinityTools
    
    style Browser fill:#87CEEB
    style Memory fill:#87CEEB
    style Retro fill:#87CEEB
    style Verify fill:#87CEEB
    style WP fill:#FFA07A
    style FTP fill:#FFA07A
    style Deploy fill:#FFA07A
```

---

## 12. Session Lifecycle (Example Project-style THINK→DEPLOYED)

```mermaid
sequenceDiagram
    participant U as User
    participant V as Vendor Harness
    participant S as Trinity Shim
    participant K as Kernel
    participant Tool as CLI Tool
    participant Verify as Verifier
    participant Mem as Memory
    
    U->>V: lll
    V->>S: skill 'lll' triggered
    S->>K: trinity-shell lll
    K->>Mem: search recent context
    Mem-->>K: top 5 retros
    K-->>S: status + memory hints
    S-->>V: rendered status
    V-->>U: 📊 status report
    
    U->>V: vvv "fix login bug"
    V->>S: skill 'vvv'
    S->>Mem: search "login bug"
    Mem-->>S: 3 similar past
    S->>U: 5 questions + past hints
    U->>S: answers
    S->>Verify: verify session
    Verify-->>S: PASS
    
    U->>V: nnn
    V->>S: skill 'nnn'
    S->>K: create plan with context
    K-->>S: plan
    S-->>U: plan for approval
    
    U->>V: gogogo
    V->>S: skill 'gogogo'
    S->>K: loop start
    
    loop Each goal
        K->>Tool: execute (browser-cli/etc)
        Tool-->>K: result
        K->>Verify: verify
        Verify-->>K: PASS/RETRY/...
    end
    
    K-->>S: all done
    S-->>V: summary
    
    U->>V: rrr
    V->>S: skill 'rrr'
    S->>K: write retro
    K->>Mem: learn (auto-index)
    Mem-->>K: indexed
    K-->>U: ✅ Done
```

---

## 13. Audit Hash Chain

```mermaid
graph LR
    E1[Event 1<br/>prev: null<br/>hash: H1]
    E2[Event 2<br/>prev: H1<br/>hash: H2]
    E3[Event 3<br/>prev: H2<br/>hash: H3]
    E4[Event N<br/>prev: H_n-1<br/>hash: H_n]
    
    E1 --> E2
    E2 --> E3
    E3 -.-> E4
```

```text
events.ndjson:

{ "ts": "...", "event": "session_start", "prev_hash": null, "hash": "abc..." }
{ "ts": "...", "event": "vvv_pass", "prev_hash": "abc...", "hash": "def..." }
{ "ts": "...", "event": "tool_call", "prev_hash": "def...", "hash": "ghi..." }
{ "ts": "...", "event": "verify_verdict", "prev_hash": "ghi...", "hash": "jkl..." }
...

Tampering detection:
  rebuild hashes → if mismatch = log corrupted
```

---

## 14. Phase Roadmap (10 phases)

```mermaid
gantt
    title Trinity OS Evolution Roadmap
    dateFormat YYYY-MM-DD
    section Foundation
    Phase 0 Vocabulary :done, p0, 2026-04-28, 1d
    Phase 0.5 Bootstrap Pack :p05, after p0, 14d
    Phase 1 Tool Contract :p1, after p05, 14d
    section Brain
    Phase 2 memory-cli :p2, after p1, 14d
    Phase 3 Wire memory :p3, after p2, 7d
    section Judge
    Phase 4 verify-cli :p4, after p3, 14d
    section Loop
    Phase 5 Goal/Loop :p5, after p4, 14d
    Phase 6 Graph YAML :p6, after p5, 14d
    section Polish
    Phase 7 retro-cli :p7, after p6, 7d
    Phase 8 Shim :p8, after p7, 14d
    Phase 9 Hybrid memory :p9, after p8, 21d
    Phase 10 Extension platform :p10, after p9, 30d
```

---

## 15. Vendor Adapter Comparison

```mermaid
graph LR
    subgraph CC["Claude Code"]
        CCS[Skills]
        CCH[Hooks]
        CCM[MCP]
        CCC[Commands]
    end
    
    subgraph CX["Codex CLI"]
        CXA[AGENTS.md]
        CXT[Tool config]
    end
    
    subgraph CR["Cursor"]
        CRR[Rules MDC]
        CRC[Commands]
    end
    
    subgraph GM["Gemini CLI"]
        GMM[GEMINI.md]
        GMS[System prompt]
    end
    
    Trinity[Trinity Shim<br/>Universal] --> CC
    Trinity --> CX
    Trinity --> CR
    Trinity --> GM
    
    style CC fill:#90EE90
    style CX fill:#FFD700
    style CR fill:#FFD700
    style GM fill:#FFA500
```

```text
Capability matrix:

                    │ Claude Code │ Codex CLI │ Cursor │ Gemini CLI │
────────────────────┼─────────────┼───────────┼────────┼────────────┤
Slash commands      │     ✅       │    ⚠️      │   ⚠️    │     ❌      │
Pre-response hooks  │     ✅       │    ❌      │   ❌    │     ❌      │
Post-response hooks │     ✅       │    ❌      │   ❌    │     ❌      │
Tool call hooks     │     ✅       │    ⚠️      │   ❌    │     ❌      │
Permission UX       │     ✅       │    ⚠️      │   ⚠️    │     ❌      │
Streaming           │     ✅       │    ✅      │   ✅    │     ✅      │
MCP support         │     ✅       │    ❌      │   ⚠️    │     ❌      │
Custom prompt       │     ✅       │    ✅      │   ✅    │     ✅      │

→ Claude Code = best harness for Trinity shim
```

---

## 16. Data Flow — From Goal to Memory

```mermaid
flowchart LR
    Goal[Goal] --> Decompose[Decompose<br/>vendor AI]
    Decompose --> Tree[Goal Tree]
    Tree --> Loop{Loop}
    Loop --> Tools[CLI Tools]
    Tools --> Artifacts[Artifacts<br/>files + sha256]
    Artifacts --> Verify[Verify-cli]
    Verify -->|PASS| Continue[Next goal]
    Verify -->|RETRY| Loop
    Verify -->|DEAD/HUMAN| Escalate
    Continue --> Loop
    Loop --> Done[All done]
    Done --> Retro[retro-cli]
    Retro --> MemIndex[memory-cli index]
    MemIndex --> Brain[(Knowledge Brain)]
    Brain -.future context.-> Decompose
```

---

## 17. State Persistence — File Layout

```text
.ai/
├── ssot.yaml                          ← project SSOT
├── tools.yaml                         ← tool registry
├── shim-config.yaml                   ← shim adapter config
│
├── policies/
│   ├── safety.yaml                    ← forbidden patterns
│   ├── verifier-rules.yaml            ← Judge rules
│   ├── loop-budget.yaml               ← budget limits
│   └── llm_judge.yaml                 ← when to invoke LLM judge
│
├── graphs/
│   ├── standard.yaml                  ← default workflow
│   ├── deploy.yaml                    ← deployment workflow
│   ├── seo.yaml                       ← SEO workflow
│   └── conditions.yaml                ← shared conditions
│
├── schemas/
│   ├── envelope-v1.schema.json
│   ├── verifier-rules.schema.json
│   ├── goal.schema.json
│   ├── loop_state.schema.json
│   └── retro-frontmatter.schema.json
│
├── audit/
│   ├── events.ndjson                  ← hash-chain log
│   ├── signatures/                    ← cryptographic proofs
│   └── llm-judge/                     ← LLM judge prompts/responses
│
├── sessions/
│   ├── active/                        ← symlink to current
│   └── <session-id>/
│       ├── .id
│       ├── 00_CONTEXT.md
│       ├── 01_PROMPT.md
│       ├── 02_PLAN.md
│       ├── 99_SUMMARY.md
│       ├── goals.yaml                 ← goal tree
│       ├── loop_state.json            ← runtime state
│       ├── checkpoints/
│       └── DO/
│           ├── snapshot/              ← read-only
│           ├── dev/                   ← work here
│           └── prod/                  ← after promote
│
└── cli/
    └── (Python kernel commands)
```

---

## 18. Composability Example — Pipe + Chain

```text
User wants: "Find auth bug, fix it, deploy with backup"

Step 1: Search memory
  trinity-shell consult "auth bug" --json | jq '.data.results'

Step 2: Get specific past retro
  memory-cli get r_2025-11-25_auth-fix --json

Step 3: Open browser for manual repro
  browser-cli --cmd "goto /backend/login ; screenshot ; eval 'document.title'"

Step 4: Run verify before fix
  verify-cli --cmd "verify --rule-set=code_change"

Step 5: Apply fix in dev
  (vendor AI uses Edit tool to modify code)

Step 6: Verify code change
  verify-cli --cmd "verify --rule-set=code_change"

Step 7: Promote to prod
  trinity loop transition promote_request --human-approval=YES

Step 8: Backup before deploy
  deploy-cli --cmd "backup ; deploy --env=prod"

Step 9: Verify deployment
  verify-cli --cmd "verify --rule-set=deploy_check"

Step 10: Write retro + index
  retro-cli --cmd "create --session=$SESSION_ID"
  retro-cli --cmd "commit RETRO.md"   # auto memory-cli index
```

---

## 19. Quick Visual Cheat Sheet

```text
🪞 Harness    = Vendor (Claude Code / Codex / Cursor / Gemini)
🔌 Shim       = trinity-shell + adapters (.claude/skills, AGENTS.md, ...)
⚙️  Kernel     = Trinity (sessions, locks, audit, policy)
🧠 Brain      = ai-docs + memory-cli (FTS5)
🛠 Organs     = browser-cli, verify-cli, retro-cli, ftp-cli, ...
⚖️  Judge      = verify-cli + verifier-rules.yaml
📜 Truth      = artifacts + events.ndjson (hash-chain)
🌀 Loop       = goal tree + checkpoint/resume
🕸 Graph      = workflow.yaml + transition authority
```

---

## 20. Mind Model (One Picture)

```text
                    ┌─────────────┐
                    │   👤 USER   │
                    └──────┬──────┘
                           │ goals
                           ▼
                ┌──────────────────────┐
                │   🪞 VENDOR HARNESS  │  ← reasoning + LLM
                │   (Claude/Codex/...)  │
                └──────────┬───────────┘
                           │ slash commands
                           ▼
                ┌──────────────────────┐
                │   🔌 TRINITY SHIM     │  ← bridge
                └──────────┬───────────┘
                           │ shells out
                           ▼
                ┌──────────────────────┐
                │   ⚙️  TRINITY KERNEL │  ← coordinator + judge
                │  • loop              │
                │  • graph             │
                │  • verify            │
                │  • policy            │
                │  • audit             │
                └────┬───────────┬─────┘
                     │           │
                     ▼           ▼
              ┌──────────┐  ┌─────────────┐
              │🧠 BRAIN  │  │ 🛠 ORGANS   │
              │ai-docs   │  │ browser-cli │
              │memory-cli│  │ memory-cli  │
              │retros    │  │ verify-cli  │
              │lessons   │  │ retro-cli   │
              │          │  │ ftp-cli     │
              └──────────┘  └─────────────┘
                     │           │
                     └─────┬─────┘
                           ▼
                  ┌────────────────┐
                  │ 📜 ARTIFACTS    │  ← truth
                  │ events.ndjson  │     (hash-chain)
                  └────────────────┘
```

---

## See also

- [`00_BLUEPRINT.md`](00_BLUEPRINT.md) — Master spec
- All other specs (each has its own diagrams inline)

## Changelog

- **v1.0.0 (2026-04-28)** — Initial diagrams collection

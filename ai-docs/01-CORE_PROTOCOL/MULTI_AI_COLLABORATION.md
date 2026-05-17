# 🤝 Multi-AI Collaboration Guide

**Purpose**: Coordination protocol for multiple AI agents working together
**Agents**: Gemini (Architect), Codex (Technical), Claude (Safety)
**Updated**: 2025-12-18
**Version**: 1.0.0

---

## Agent Roles & Responsibilities

### 🟦 Gemini (The Architect)
**Strengths**:
- System design and architecture
- High-level planning and coordination
- Structure and organization
- Documentation generation (INDEX.md, etc.)

**Responsibilities**:
- Define overall project structure
- Coordinate between agents
- Generate documentation indices
- Resolve architectural conflicts

**Tools**:
- Gemini CLI
- Analysis and synthesis
- Long-context understanding

---

### ⬛ Codex (The Builder)
**Strengths**:
- Technical implementation
- Code correctness and validation
- Automation scripts (bash, python)
- Pattern detection and fixing

**Responsibilities**:
- Implement technical solutions
- Write automation scripts (setup.sh, enforce.sh)
- Validate code examples
- Fix technical errors

**Tools**:
- Code analysis
- Script writing
- Regex patterns
- Technical validation

---

### 🟧 Claude (The Safety Officer)
**Strengths**:
- Safety and security analysis
- Process compliance
- Risk assessment (Red Team)
- Documentation quality

**Responsibilities**:
- Define safety gates and rules
- Review for security issues
- Ensure compliance with standards
- Document lessons learned

**Tools**:
- Claude Code
- Retrospective analysis
- Red Team methodology
- Safety protocol design

---

## Collaboration Patterns

### Pattern 1: Analysis → Design → Implementation

**Use When**: Building new features or major refactors

**Flow**:
```
1. Gemini (Analysis)
   ↓ Defines architecture and structure
2. Claude (Safety Review)
   ↓ Identifies risks and safety requirements
3. Codex (Implementation)
   ↓ Builds the solution
4. Claude (Verification)
   ↓ Reviews for compliance
5. Gemini (Integration)
   ↓ Merges into overall system
```

**Example**: Creating 01-CORE_PROTOCOL structure
- Gemini proposed structure
- Claude defined SAFETY_GATES.md requirements
- Codex implemented automation scripts
- Claude reviewed safety compliance
- Gemini coordinated final structure

---

### Pattern 2: Parallel Analysis (Multi-Perspective)

**Use When**: Complex problems needing multiple viewpoints

**Flow**:
```
Problem Statement
    ↓
┌─────────┬─────────┬─────────┐
│ Gemini  │ Codex   │ Claude  │
│ (Arch)  │ (Tech)  │ (Safety)│
└─────────┴─────────┴─────────┘
    ↓         ↓         ↓
  Analysis  Analysis  Analysis
    └─────────┬─────────┘
         Synthesis
         (Consensus)
```

**Example**: Shipping Fee Bug (2025-12-17)
- **Gemini**: Analyzed architecture (Hybrid Approach)
- **Codex**: Analyzed implementation (SQL, models, views)
- **Claude**: Analyzed safety (data integrity, user impact)
- **Result**: 90% consensus on root causes, comprehensive fix

**Outcomes**:
- ✅ 360° perspective
- ✅ No blind spots
- ⚠️ May have conflicting recommendations (needs synthesis)

---

### Pattern 3: Sequential Handoff (Pipeline)

**Use When**: Clear dependencies between tasks

**Flow**:
```
Gemini (Define structure)
    ↓ hands off to
Codex (Implement scripts)
    ↓ hands off to
Claude (Document & verify)
```

**Example**: setup.sh Creation
1. **Gemini**: Defined config.json structure
2. **Codex**: Implemented setup.sh script
3. **Claude**: Documented ENV_VARS.md + UX review

**Handoff Protocol**:
```markdown
From: Gemini
To: Codex
Task: Implement setup.sh
Context: See workspace_gemini/draft_context_config.json
Requirements: Interactive wizard, validation, .env generation
Expected Output: workspace_codex/draft_setup.sh
```

---

## Agent-to-Agent Communication

### Handoff Template

```markdown
## Task Handoff

**From**: [Agent Name]
**To**: [Agent Name]
**Date**: [YYYY-MM-DD HH:MM]

### Task
[Clear task description]

### Context
- **Files to reference**: [list]
- **Requirements**: [bullet points]
- **Constraints**: [safety rules, limitations]

### Expected Output
- **Deliverable**: [file path]
- **Format**: [markdown, script, code]
- **Timeline**: [estimate]

### Questions/Clarifications
[Any ambiguities to resolve]

---
**Status**: 🟡 Pending / 🔵 In Progress / ✅ Complete
```

---

### Progress Updates

**Use**: `.ai/sessions/{date}/WORK_PLAN.md` work log

**Format**:
```markdown
- **[Time] [Agent]**: ✅ **STATUS** - Brief description. Key outcomes. Next steps.
```

**Example**:
```markdown
- **2025-12-18 19:40 [Claude]**: ✅ ENV_VARS.md CREATED - Documented 8 variables. Ready for Codex's enforce.sh integration.
```

---

## Consensus Building

### When Agents Disagree

**Process**:
1. **Document Disagreement**
   - Each agent states position
   - Provide reasoning
   - List pros/cons

2. **Seek Synthesis**
   - Gemini (Architect) facilitates
   - Look for compromise
   - Identify non-negotiables

3. **Resolution Strategies**:
   - **Hybrid Approach**: Combine best of both (e.g., Manual + Automated safety)
   - **Experiment**: Try approach A on dev, if fails try B
   - **Defer to Expert**: Safety → Claude, Technical → Codex, Structure → Gemini
   - **User Decision**: Present options, let user choose

**Example**: Safety Approach Conflict (Round 2)
- **Claude**: Manual feedback loop every deploy
- **Codex/Gemini**: Automated tests
- **Resolution**: Hybrid (Auto default, Manual for high-risk)

---

## Quality Assurance (Cross-Review)

### Review Protocol

**After Each Deliverable**:
```
Creator: Codex (implements setup.sh)
    ↓
Reviewer 1: Claude (safety check - any risks?)
    ↓
Reviewer 2: Gemini (integration check - fits structure?)
    ↓
Approval: If 2/3 approve → Accept
```

**Review Checklist**:
- [ ] Meets requirements?
- [ ] Follows standards (UNIVERSAL_RULES.md)?
- [ ] Passes safety gates?
- [ ] Integrates with existing system?
- [ ] Documented sufficiently?

---

## Conflict Resolution

### Types of Conflicts

**Technical Conflict**:
- **Example**: "Use PHP array vs {{FRAMEWORK}} query builder"
- **Resolver**: Codex (technical expert)
- **Criteria**: Performance, maintainability, project standards

**Safety Conflict**:
- **Example**: "Skip backup for minor change?"
- **Resolver**: Claude (safety officer)
- **Criteria**: Risk level, recovery options, user impact

**Architectural Conflict**:
- **Example**: "Monolith vs modular structure"
- **Resolver**: Gemini (architect)
- **Criteria**: Scalability, maintainability, complexity

---

### Escalation Path

```
Agent-level disagreement
    ↓ (cannot resolve)
Supervisor review (Gemini HP)
    ↓ (still unclear)
User decision
```

---

## Collaboration Anti-Patterns

### ❌ DON'T: Work in Silos

**Bad**:
```
Gemini works → delivers → Codex starts from scratch
(No context sharing, duplicated analysis)
```

**Good**:
```
Gemini analyzes → documents findings → Codex reads & builds on insights
(Shared context, faster execution)
```

---

### ❌ DON'T: Duplicate Work

**Bad**:
```
Both Codex and Claude create validation scripts
(Wasted effort, conflicting implementations)
```

**Good**:
```
Assign clearly: Codex = enforce.sh, Claude = ENV_VARS.md documentation
(Clear ownership, no overlap)
```

---

### ❌ DON'T: Silent Disagreement

**Bad**:
```
Claude thinks approach X is unsafe but says nothing
(Hidden risks, later failures)
```

**Good**:
```
Claude raises concern: "Approach X risks Y - suggest Z instead"
(Transparent, opportunity for discussion)
```

---

## Success Patterns (From AI Trinity Session)

### Pattern: Structured Phases

**Phase 1**: Audit & Analysis
- All agents read assigned documents
- Each analyzes from their perspective
- Share findings in Discussion Round 1

**Phase 2**: Synthesis & Consensus
- Gemini synthesizes findings
- Team resolves conflicts
- Consensus documented

**Phase 3**: Parallel Execution
- Each agent works on assigned tasks
- Regular status updates
- Cross-review deliverables

**Result**: Efficient, minimal conflicts, high quality

---

### Pattern: Red Team Review

**Process**:
1. Agent proposes solution
2. Another agent plays "Red Team"
3. Try to break the proposal
4. Identify weaknesses
5. Strengthen solution

**Example**: Round 1 → Round 2
- Round 1: Constructive proposals
- Round 2: Claude Red Team (found 10+ weaknesses)
- Result: Much stronger final plan

---

### Pattern: Self-Correction

**Process**:
1. Agent creates initial deliverable
2. Reviews other agents' feedback
3. Acknowledges mistakes
4. Revises deliverable
5. Documents learnings

**Example**: Claude's Score Revision
- Initial: 7.2/10 (optimistic bias)
- Feedback: Team points out issues
- Revision: 6.5/10 (realistic)
- Learning: Automation > Documentation

---

## Handoff Scenarios

### Scenario 1: Gemini → Codex (Structure → Implementation)

**Gemini Delivers**:
- Architectural design
- File structure proposal
- Requirements specification

**Codex Receives**:
- Reads design docs
- Asks clarifying questions
- Implements according to spec
- Flags technical impossibilities

**Handoff File**: `workspace_gemini/ARCH_SPEC_FOR_CODEX.md`

---

### Scenario 2: Codex → Claude (Implementation → Safety Review)

**Codex Delivers**:
- Working script/code
- Test results
- Technical documentation

**Claude Receives**:
- Reviews for security issues
- Checks compliance with SAFETY_GATES
- Tests edge cases
- Suggests safety improvements

**Handoff File**: `workspace_codex/IMPLEMENTATION_FOR_REVIEW.md`

---

### Scenario 3: Claude → Gemini (Safety → Integration)

**Claude Delivers**:
- Safety requirements
- Risk assessment
- Compliance checklist

**Gemini Receives**:
- Integrates safety into architecture
- Updates structure if needed
- Ensures safety gates enforced

**Handoff File**: `workspace_claude/SAFETY_REQUIREMENTS.md`

---

## Metrics & Tracking

### Collaboration Metrics

**Quality Metrics**:
- Consensus rate (% of decisions agreed upon)
- Conflict resolution time (minutes to resolve)
- Cross-review coverage (% of deliverables reviewed)

**Efficiency Metrics**:
- Handoff turnaround time
- Parallel vs sequential ratio
- Rework rate (% of deliverables requiring revision)

**From AI Trinity Session**:
- Consensus: 100% on 6 must-dos
- Conflicts: 3 (all resolved within 1 hour)
- Cross-review: 100% (all agents reviewed each other's scores)
- Parallel work: High (scoring done simultaneously)

---

## Best Practices

### ✅ DO:

1. **Document Handoffs**: Use template above
2. **Share Context**: Reference files, not assumptions
3. **Acknowledge Receipt**: Confirm understanding before starting
4. **Status Updates**: Regular progress reports in WORK_PLAN.md
5. **Cross-Review**: Review each other's work
6. **Respect Expertise**: Defer to specialist in their domain
7. **Transparent Disagreement**: Voice concerns early
8. **Learn from Feedback**: Accept criticism, revise work

---

### ❌ DON'T:

1. **Assume Context**: Always verify understanding
2. **Work in Parallel Without Coordination**: Check for overlaps
3. **Skip Documentation**: Every handoff needs context
4. **Ignore Feedback**: Team input is valuable
5. **Defend Ego**: Goal is best outcome, not "being right"
6. **Silent Failures**: Report blockers immediately
7. **Change Scope Without Notice**: Coordinate scope changes
8. **Deliver Without Review**: Get at least one peer review

---

## Tools for Collaboration

### Shared Workspace

**Structure**:
```
.ai/sessions/{date}_{topic}/
├── WORK_PLAN.md              ← Central coordination
├── artifacts/
│   ├── 01_KICKOFF.md         ← Meeting notes
│   ├── 02_DISCUSSION_R1.md   ← Round 1 discussion
│   └── 02_DISCUSSION_R2.md   ← Round 2 synthesis
├── workspace_gemini/         ← Gemini's drafts
├── workspace_codex/          ← Codex's drafts
├── workspace_claude/         ← Claude's drafts
└── workspace_shared/         ← Joint deliverables
```

**Rules**:
- Each agent owns their workspace
- Shared workspace for joint work
- WORK_PLAN.md = single source of status
- Artifacts = discussion + decisions

---

### Communication Channels

**Primary**: WORK_PLAN.md work log
- Append status updates
- Timestamp + Agent name
- Brief summary + next steps

**Secondary**: Discussion artifacts
- Detailed proposals
- Analysis documents
- Consensus building

**Emergency**: Direct file in shared workspace
- `workspace_shared/URGENT_{topic}.md`
- For critical issues needing immediate attention

---

## Real Example: AI Trinity Session (2025-12-18)

### Timeline

**17:00 - Initialization**
- Gemini: Environment setup
- Created session structure

**17:30 - Phase 1 Start**
- Claude: Readiness confirmed, started retrospectives analysis
- Codex: Began standards review
- Gemini: Scanned INDEX.md, found outdated

**18:00 - Discussion Round 1**
- All agents contributed proposals
- Identified structure for 01-CORE_PROTOCOL
- Raised concerns and questions

**18:40 - Red Team Analysis**
- Claude activated SAFETY_CRITIC mode
- Found 10+ weaknesses in proposals
- Proposed defensive architecture

**19:00 - Scoring Phase**
- All agents scored independently (parallel work)
- Claude: 7.2, Codex: 7.0, Gemini: 7.0, Gemini HP: 5.5

**19:20 - Cross-Analysis**
- Claude analyzed all scores
- Found consensus and conflicts
- Self-corrected optimistic bias

**19:40 - Execution Phase**
- Claude: Created ENV_VARS.md
- Codex: Analyzing hardcoded paths
- Gemini: Working on INDEX.md

**19:50 - Continued Execution**
- Claude: Updated SAFETY_GATES.md with enforcement levels
- Codex: Preparing enforce.sh implementation
- Gemini: Config.json refinement

---

### What Worked Well

1. **Clear Role Separation**
   - No overlap or confusion
   - Each agent focused on strengths

2. **Parallel Work**
   - Scoring done simultaneously
   - Efficient use of time

3. **Transparent Feedback**
   - Claude's Red Team analysis
   - Codex's technical critique
   - Gemini HP's brutal honesty (5.5/10)

4. **Self-Correction**
   - Claude revised score (7.2 → 6.5)
   - Acknowledged mistakes
   - Accepted team feedback

5. **Structured Discussion**
   - Round 1: Proposals
   - Round 2: Critique & synthesis
   - Clear progression

---

### Challenges & Solutions

**Challenge 1**: Conflicting Philosophies
- Claude: Manual safety emphasis
- Codex/Gemini: Automation emphasis
- **Solution**: Hybrid approach (consensus)

**Challenge 2**: Different Scoring
- Scores ranged 5.5 - 7.2
- **Solution**: Cross-analysis, team average

**Challenge 3**: Overlapping Domains
- UNIVERSAL_RULES vs SAFETY_GATES
- **Solution**: Define severity levels (BLOCKER/WARNING/MANUAL)

---

## Anti-Patterns Observed

### From Real Sessions

**❌ Codex's Over-Complication** (Shipping Fee Bug):
- Created complex if-else logic
- Backend had simple solution
- **Lesson**: Check existing working code first

**❌ Claude's Optimistic Bias** (Scoring):
- Gave 7.2 vs reality 6.5
- Downplayed enforcement issues
- **Lesson**: Be realistic, accept harsh feedback

**❌ Missing Schema Verification** (Multiple Sessions):
- Assumed column exists
- Got "Unknown column" error
- **Lesson**: Always SHOW COLUMNS before SELECT

---

## Coordination Protocols

### Starting Collaboration

1. **Define Scope** (Gemini leads)
   - What are we building?
   - Success criteria?
   - Timeline?

2. **Assign Roles**
   - Who does what?
   - Clear boundaries
   - Identify dependencies

3. **Establish Communication**
   - Where to update status?
   - How often?
   - What format?

4. **Set Standards**
   - Which SAFETY_GATES apply?
   - Code style to follow?
   - Documentation format?

---

### During Collaboration

1. **Regular Status Updates** (every 30-60 minutes)
   ```markdown
   [Time] [Agent]: [Status] - [What done]. [Next]. [Blockers if any].
   ```

2. **Raise Blockers Immediately**
   ```markdown
   🚨 BLOCKER [Agent]: [Issue]. Needs [resolution]. Blocking [task].
   ```

3. **Request Reviews**
   ```markdown
   📝 REVIEW REQUEST [Agent]: Completed [deliverable]. Please review for [aspect].
   ```

4. **Share Learnings**
   ```markdown
   💡 INSIGHT [Agent]: Discovered [finding]. May impact [other work].
   ```

---

### Ending Collaboration

1. **Final Synthesis** (Gemini leads)
   - Consolidate all deliverables
   - Create summary document
   - Identify lessons learned

2. **Quality Check** (All agents)
   - Cross-review final outputs
   - Verify all tasks complete
   - Check for gaps

3. **Retrospective** (Claude leads)
   - What went well?
   - What could improve?
   - Action items for next time

4. **Archive Session**
   ```bash
   # Move to archive
   mv .ai/sessions/2025-12-18_* .ai/sessions/archive/

   # Or keep active for reference
   ```

---

## Task Assignment Matrix

### Who Does What

| Task Type | Primary | Review | Coordinate |
|-----------|---------|--------|------------|
| Architecture Design | Gemini | Claude | - |
| Script Implementation | Codex | Claude | Gemini |
| Safety Analysis | Claude | Codex | - |
| Documentation Structure | Gemini | Claude | - |
| Code Validation | Codex | Claude | - |
| Risk Assessment | Claude | Gemini | - |
| Integration | Gemini | All | - |
| Retrospective | Claude | All | - |

---

## Consensus vs Expertise

### When to Seek Consensus (All Agents)
- Major architectural decisions
- Structure changes affecting all
- Standards that everyone must follow
- Severity level definitions

### When to Defer to Expert (Single Agent)
- **Security questions** → Claude
- **Technical correctness** → Codex
- **System design** → Gemini
- **Automation patterns** → Codex
- **Safety protocols** → Claude
- **Integration strategy** → Gemini

**Rule**: Don't bikeshed in expert's domain

---

## Success Metrics

### Collaboration Quality

**Excellent (9+/10)**:
- 100% consensus on critical decisions
- Conflicts resolved within 1 hour
- All deliverables cross-reviewed
- Zero duplicate work
- Fast handoff (<30m turnaround)

**Good (7-8/10)**:
- 80%+ consensus
- Most conflicts resolved
- Majority cross-reviewed
- Minimal duplication

**Poor (<6/10)**:
- Low consensus
- Unresolved conflicts
- Little cross-review
- Frequent duplications

**AI Trinity Session Score**: 8.5/10 (Excellent collaboration)

---

## Templates

### Quick Status Update
```markdown
[Claude]: ✅ Task X done. Files: [list]. Next: Task Y (15m).
```

### Handoff
```markdown
From: [Me] → To: [You]
Task: [Description]
Context: [Files to read]
Output: [Expected deliverable]
```

### Review Request
```markdown
📝 Review: [File/deliverable]
Aspect: [Safety/Technical/Integration]
Urgency: [Normal/Urgent]
```

### Blocker Report
```markdown
🚨 BLOCKER: [Issue]
Impact: [What's blocked]
Need: [Resolution required]
```

---

## Summary

**Key Principles**:
1. **Clear Roles**: Each agent has expertise
2. **Transparent Communication**: Share context, raise issues early
3. **Respect Expertise**: Defer to specialist in their domain
4. **Cross-Review**: Peer review improves quality
5. **Self-Correction**: Accept feedback, revise work
6. **Document Everything**: Handoffs, decisions, learnings

**Collaboration Formula**:
```
Clear Roles + Open Communication + Mutual Review + Self-Correction
= High-Quality Outcomes
```

---

**Version**: 1.0.0
**Created**: 2025-12-18
**By**: Claude (AI Trinity - Safety Officer)
**Based On**: AI Trinity Session 2025-12-18 (real collaboration patterns)
**Status**: Production-ready

# Trinity AI-Assisted Setup Guide

**For AI Agents: How to Help Users Install Trinity in New Projects**

---

## 🤖 AI Agent Instructions

When a user asks to install Trinity in their project, follow this workflow:

---

## 📋 Setup Workflow for AI

### Phase 1: Understand Context (1 minute)

**Ask user:**
1. "What is your project path?" → Get `PROJECT_PATH`
2. "Do you have Python 3.8+ installed?" → Verify prerequisites
3. "Is this a git project?" → Determine .gitignore needs

**Store:**
```
PROJECT_PATH = /path/to/user/project
TRINITY_SOURCE = /path/to/your/project/.ai
HAS_GIT = yes/no
```

---

### Phase 2: Pre-Installation Checks (30 seconds)

**Run checks:**

```bash
# 1. Verify project exists
test -d PROJECT_PATH && echo "✅ Project exists" || echo "❌ Project not found"

# 2. Check if .ai already exists
test -d PROJECT_PATH/.ai && echo "⚠️ .ai exists" || echo "✅ Ready to install"

# 3. Check Python
python3 --version
# Should be 3.8+

# 4. Check Trinity source
test -d TRINITY_SOURCE && echo "✅ Trinity source found" || echo "❌ Source not found"
```

**Report to user:**
```
✅ All checks passed - ready to install
or
⚠️ Issue found: [explain issue]
```

---

### Phase 3: Installation (2 minutes)

**Execute:**

```bash
# 1. Navigate
cd PROJECT_PATH

# 2. Copy Trinity
cp -r TRINITY_SOURCE .ai
echo "✅ Copied Trinity files"

# 3. Update config
cd .ai

# Get absolute project path
PROJECT_ABS=$(cd .. && pwd)

# Update ssot.yaml
sed -i.bak "s|project_root: \".*\"|project_root: \"$PROJECT_ABS\"|" ssot.yaml
rm ssot.yaml.bak
echo "✅ Updated project_root to: $PROJECT_ABS"

# 4. Install dependencies
bash setup.sh
echo "✅ Dependencies installed"
```

**Show user:**
```
Installation progress:
├─ ✅ Files copied
├─ ✅ Config updated
└─ ✅ Dependencies installed
```

---

### Phase 4: Validation (30 seconds)

**Run tests:**

```bash
cd .ai
source .venv/bin/activate

# 1. Test CLI
python3 -m cli.main --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ CLI working"
else
    echo "❌ CLI failed"
    exit 1
fi

# 2. Run selftest
python3 -m cli.main verify selftest
# Should show: ✅ All self-tests passed!
```

**Report:**
```
Validation Results:
├─ ✅ CLI accessible
├─ ✅ Selftest passed (3/3)
└─ ✅ Trinity ready to use
```

---

### Phase 5: First Session Demo (1 minute)

**Create demo session:**

```bash
cd .ai
source .venv/bin/activate

# Create session
python3 -m cli.main session new "Trinity Setup Verification"

# Show structure
ls -la sessions/2025-*/
```

**Explain to user:**
```
📁 Your first session created:
   sessions/2025-12-21_trinity_setup_verification/

Structure:
├── THINK/      - Plan your work here
├── DO/         - Work here (dev folder)
├── CONTROL/    - Monitor status here
└── .ai/state/  - System state (don't edit)

Next: Run 'ai snapshot' to capture current project state
```

---

### Phase 6: Handoff to User (Final)

**Provide:**

1. **Quick Start Commands:**
```bash
# All commands must run from .ai/ directory
cd PROJECT_PATH/.ai
source .venv/bin/activate

# Your first workflow:
python3 -m cli.main session new "Your Task"
python3 -m cli.main snapshot run
# ... edit DO/dev/ ...
python3 -m cli.main verify run --scope dev
python3 -m cli.main promote run
python3 -m cli.main verify run --scope prod
python3 -m cli.main close run
```

2. **Documentation Links:**
```
📖 Read next:
   - .ai/docs/USER_MANUAL.md (complete guide)
   - .ai/docs/WHAT_YOU_GET.md (benefits)
   - .ai/docs/ARCHITECTURE_DIAGRAM.md (how it works)
```

3. **Troubleshooting:**
```
Common issues:
- "SSOT not found" → cd to .ai/ directory first
- "Module not found" → source .venv/bin/activate
- "Selftest fails" → Check tests/verify_fixtures/ exists
```

---

## 🎯 AI Agent Conversation Template

### When User Says: "Help me install Trinity"

**AI Response:**

```
I'll help you install Trinity Protocol in your project!

First, I need some information:
1. What is your project path? (e.g., /Users/you/my-project)
2. Do you have Python 3.8+ installed?
3. Is this a git project?

After you answer, I'll:
✅ Copy Trinity files
✅ Update configuration
✅ Install dependencies
✅ Run validation tests
✅ Create your first session

Estimated time: 5 minutes
```

---

### Installation Steps (AI executes)

```
Step 1: Checking prerequisites...
[Run checks]
✅ All prerequisites met

Step 2: Copying Trinity files...
[cp -r command]
✅ Files copied (104 files, 49 directories)

Step 3: Updating configuration...
[sed command]
✅ project_root updated to: /your/project

Step 4: Installing dependencies...
[bash setup.sh]
✅ Installed: typer, rich, PyYAML

Step 5: Validating installation...
[selftest]
✅ CLI working
✅ Selftest: 3/3 passed

✅ Trinity installed successfully!

Next steps:
1. cd .ai
2. source .venv/bin/activate
3. python3 -m cli.main session new "Your First Task"

📖 Full guide: .ai/docs/USER_MANUAL.md
```

---

## 🔧 AI Troubleshooting Guide

### Issue 1: "User's project path has spaces"

```bash
# Handle spaces in paths
PROJECT_PATH="/Users/name/My Documents/project"

# Use quotes in commands
cp -r "$TRINITY_SOURCE" "$PROJECT_PATH/.ai"
cd "$PROJECT_PATH/.ai"
```

---

### Issue 2: "Python version too old"

```python
# Check version
import sys
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required")
    print(f"Current: {sys.version}")
    print("Please upgrade Python")
```

---

### Issue 3: "Permission denied"

```bash
# Check permissions
if [ ! -w "$PROJECT_PATH" ]; then
    echo "❌ No write permission"
    echo "Run: chmod u+w $PROJECT_PATH"
fi
```

---

### Issue 4: "Trinity source not found"

**AI should ask:**
```
Trinity source not found at expected location.

Options:
1. Download Trinity:
   git clone https://github.com/yourname/trinity-protocol.git

2. Specify custom path:
   Where is your Trinity installation?

3. Install from template:
   I can download the latest release for you.
```

---

## 📝 AI Checklist (Execute in Order)

```markdown
Trinity Installation Checklist for AI Agent:

## Pre-Installation
- [ ] Get project path from user
- [ ] Verify Python 3.8+ available
- [ ] Check Trinity source exists
- [ ] Check .ai doesn't already exist

## Installation
- [ ] Copy .ai folder to project
- [ ] Update ssot.yaml with correct project_root
- [ ] Run setup.sh
- [ ] Verify venv created
- [ ] Confirm dependencies installed

## Validation
- [ ] Test CLI help command
- [ ] Run selftest (should pass 3/3)
- [ ] Create test session
- [ ] Verify session structure
- [ ] Show status command

## Documentation
- [ ] Point user to USER_MANUAL.md
- [ ] Show quick start commands
- [ ] Explain next steps

## Cleanup
- [ ] Remove test session (if created)
- [ ] Verify no errors in logs

✅ Installation complete!
```

---

## 🤝 AI-User Collaboration Example

### User: "Help me install Trinity in my project"

**AI:**
```
I'll help you install Trinity!

First, let me understand your setup:
1. What is your project path?
2. Do you have Python 3.8 or higher?
3. Is this a git repository?
```

**User:**
```
1. /Users/me/myapp
2. Yes, Python 3.10
3. Yes
```

**AI:**
```
Perfect! Let me install Trinity for you.

[Runs commands...]

✅ Installation complete!

Summary:
- Trinity installed at: /Users/me/myapp/.ai
- Configuration updated for your project
- All tests passed (3/3)
- First session created: 2025-12-21_trinity_setup_verification

Your Trinity is ready!

Quick start:
  cd /Users/me/myapp/.ai
  source .venv/bin/activate
  python3 -m cli.main session new "Your Task"

📖 Full guide: .ai/docs/USER_MANUAL.md
🏗️ Architecture: .ai/docs/ARCHITECTURE_DIAGRAM.md
💡 Benefits: .ai/docs/WHAT_YOU_GET.md
```

---

## 🎓 What AI Should Know

### Trinity Basics

**What it is:**
- Dev→Prod workflow management system
- 7 CLI commands
- 3 safety gates
- Session-based organization

**What it does:**
- Isolates work sessions
- Verifies safety (secrets, forbidden files)
- Automates promotion (dev→prod)
- Tracks workflow progress

**What user gets:**
- Safe deployments
- No manual copying
- Audit trail
- Status monitoring

---

### Key Files to Explain

**ssot.yaml** - Configuration file
- Most important: `project_root` path
- Optional: deploy targets
- Must be absolute path

**requirements.txt** - Dependencies
- typer (CLI framework)
- rich (pretty output)
- PyYAML (config parser)

**setup.sh** - Auto-installer
- Creates venv
- Installs dependencies
- Validates installation

---

### Commands to Teach User

**Essential:**
```bash
session new   # Start work
snapshot      # Capture state
verify        # Check safety
promote       # Dev → Prod
close         # Finish work
status        # Check progress
```

**Testing:**
```bash
verify selftest  # Validate Trinity
```

---

## 🔍 AI Validation Steps

After installation, AI should verify:

```python
# Pseudo-code for AI
def validate_installation(project_path):
    checks = []

    # 1. Directory structure
    checks.append(exists(f"{project_path}/.ai/cli/"))
    checks.append(exists(f"{project_path}/.ai/templates/"))
    checks.append(exists(f"{project_path}/.ai/docs/"))

    # 2. Config file
    ssot = read(f"{project_path}/.ai/ssot.yaml")
    checks.append("project_root" in ssot)

    # 3. Dependencies
    result = run("python3 -m cli.main --help")
    checks.append(result.returncode == 0)

    # 4. Selftest
    result = run("python3 -m cli.main verify selftest")
    checks.append("All self-tests passed" in result.output)

    return all(checks)
```

---

## 💡 AI Tips

### DO:
✅ Ask for project path first
✅ Verify prerequisites before starting
✅ Show progress at each step
✅ Validate installation with selftest
✅ Explain next steps clearly
✅ Point to documentation

### DON'T:
❌ Assume project path
❌ Skip validation steps
❌ Install without user confirmation
❌ Modify user's project files (only .ai/)
❌ Skip explaining what was done

---

## 📦 AI Script Template

```python
"""
Trinity Installation Script for AI Agent
"""

def install_trinity_for_user(project_path: str, trinity_source: str):
    """
    AI executes this workflow to help user install Trinity.

    Args:
        project_path: User's project directory
        trinity_source: Path to Trinity installation

    Returns:
        Success status and next steps
    """

    # Step 1: Pre-checks
    print("🔍 Checking prerequisites...")
    checks = run_prechecks(project_path, trinity_source)
    if not checks['all_pass']:
        return {"status": "error", "message": checks['errors']}

    # Step 2: Copy files
    print("📦 Copying Trinity files...")
    copy_trinity(trinity_source, f"{project_path}/.ai")

    # Step 3: Update config
    print("⚙️ Updating configuration...")
    update_config(f"{project_path}/.ai/ssot.yaml", project_path)

    # Step 4: Setup
    print("🔧 Installing dependencies...")
    run_setup(f"{project_path}/.ai")

    # Step 5: Validate
    print("✅ Validating installation...")
    validation = validate_installation(f"{project_path}/.ai")

    # Step 6: Create first session
    print("🎯 Creating demo session...")
    create_demo_session(f"{project_path}/.ai")

    return {
        "status": "success",
        "message": "Trinity installed successfully!",
        "next_steps": [
            "cd .ai",
            "source .venv/bin/activate",
            "python3 -m cli.main session new 'Your Task'",
            "Read: docs/USER_MANUAL.md"
        ]
    }
```

---

## 🎬 Conversation Flow Example

### User Request:
> "ช่วยติดตั้ง Trinity ให้หน่อย project อยู่ที่ /Users/me/myapp"

### AI Response:

```
I'll help you install Trinity in your project!

Let me verify your setup first:

[Checking prerequisites...]
✅ Python 3.10.5 found
✅ Project directory exists: /Users/me/myapp
✅ Trinity source available
✅ No existing .ai directory

[Starting installation...]

Step 1: Copying Trinity files...
  Copying: .ai/ (104 files, 49 directories)
  ✅ Done

Step 2: Updating configuration...
  Setting project_root: /Users/me/myapp
  ✅ Config updated

Step 3: Installing dependencies...
  Creating virtual environment...
  Installing: typer, rich, PyYAML
  ✅ Dependencies installed

Step 4: Validating installation...
  Testing CLI...
  ✅ CLI working

  Running selftest...
  ✅ pass_clean → PASS
  ✅ fail_secret → FAIL (expected)
  ✅ fail_forbidden → FAIL (expected)
  ✅ All tests passed!

Step 5: Creating demo session...
  ✅ Session: 2025-12-21_trinity_setup_verification

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Trinity installed successfully!

Your setup:
  Location: /Users/me/myapp/.ai
  Python: 3.10.5
  Status: Production Ready ✅

To start using Trinity:

1. cd /Users/me/myapp/.ai
2. source .venv/bin/activate
3. python3 -m cli.main session new "Your First Task"

📖 Documentation:
   - Quick Start: docs/USER_MANUAL.md
   - Benefits: docs/WHAT_YOU_GET.md
   - Architecture: docs/ARCHITECTURE_DIAGRAM.md

Need help? Just ask me or read the USER_MANUAL.md!
```

---

## 📚 AI Knowledge Base

### Key Information AI Should Know:

**1. Directory Structure:**
```
.ai/
├── cli/         - Commands (don't modify)
├── docs/        - Documentation (read to help user)
├── templates/   - Session templates (don't modify)
├── policies/    - Safety rules (can customize)
├── ssot.yaml    - Configuration (MUST update)
└── setup.sh     - Installer (run once)
```

**2. Critical Configuration:**
- `ssot.yaml` → `project_root` MUST be absolute path
- Must match actual project location
- Example: `/Users/me/myapp` NOT `~/myapp`

**3. Common Issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| "SSOT not found" | Running from wrong dir | cd .ai first |
| "Module not found" | Venv not activated | source .venv/bin/activate |
| "Selftest fails" | Fixtures missing | Copy tests/ from source |
| "Config invalid" | project_root wrong | Update ssot.yaml |

---

## 🔄 AI Update Workflow

When user asks to update Trinity:

```bash
# 1. Backup current config
cp .ai/ssot.yaml /tmp/trinity-config-backup.yaml

# 2. Backup current sessions
cp -r .ai/sessions /tmp/trinity-sessions-backup

# 3. Update core files
rm -rf .ai/cli .ai/templates .ai/docs
cp -r /path/to/new-trinity/cli .ai/
cp -r /path/to/new-trinity/templates .ai/
cp -r /path/to/new-trinity/docs .ai/

# 4. Restore config
cp /tmp/trinity-config-backup.yaml .ai/ssot.yaml

# 5. Update dependencies
cd .ai
pip install -r requirements.txt --upgrade

# 6. Validate
python3 -m cli.main verify selftest

✅ Trinity updated to v0.5 (or whatever version)
```

---

## 🎓 Teaching Points for AI

**When explaining Trinity to user:**

**1. What it solves:**
```
Before: Chat with AI → AI does stuff → Hope it's correct → Deploy → 😰
After:  Command → Trinity verifies → Safe → Deploy → 😊
```

**2. Core concept:**
```
Trinity = 3 Locks
1. 🔒 Policy (rules in yaml)
2. 🚪 Gates (auto-check)
3. ⛓️ Audit (history)

= Safe AI-assisted development
```

**3. Workflow:**
```
session → snapshot → work → verify → promote → verify → close
         └─backup   └─dev   └─safe  └─prod    └─final └─done
```

**4. Benefits:**
```
✅ No secrets in prod (auto-blocked)
✅ No .env leak (auto-filtered)
✅ No manual copy (automated)
✅ Know what to do next (status)
✅ Full history (audit)
```

---

## 🚀 Quick Installation for AI

**Simplest workflow AI can execute:**

```bash
#!/bin/bash
# AI executes this for user

# Get user's project path
read -p "Project path: " PROJECT

# Execute
cd "$PROJECT"
cp -r /path/to/your/project/.ai .
cd .ai
sed -i "s|project_root: \".*\"|project_root: \"$PROJECT\"|" ssot.yaml
bash setup.sh
source .venv/bin/activate
python3 -m cli.main verify selftest

echo "✅ Done! Run: python3 -m cli.main session new 'Task'"
```

**Time:** 2-3 minutes (mostly dependency install)

---

## 💬 AI Response Templates

### Success Response:
```
✅ Trinity installed successfully!

Installed at: /your/project/.ai
Tests passed: 3/3
Status: Ready to use

Quick start:
  cd .ai
  source .venv/bin/activate
  python3 -m cli.main session new "Your Task"

Need help? Ask me or read docs/USER_MANUAL.md
```

### Error Response:
```
❌ Installation failed

Issue: [specific error]
Cause: [explanation]

Fix:
  [step-by-step solution]

After fixing, try again or ask for help!
```

### Partial Success:
```
⚠️ Installation completed with warnings

Status:
├─ ✅ Files copied
├─ ✅ Config updated
├─ ✅ Dependencies installed
└─ ⚠️ Selftest: 2/3 passed (fail_secret pending)

This is usually okay for new projects.

You can:
1. Proceed with caution
2. Review: tests/verify_fixtures/fail_secret/
3. Ask me to investigate
```

---

## 🎯 AI Success Criteria

Installation successful when:

- [x] .ai/ directory created
- [x] ssot.yaml has correct project_root
- [x] Dependencies installed (venv exists)
- [x] CLI accessible (`--help` works)
- [x] Selftest passes (3/3)
- [x] User understands next steps

**AI should confirm:** "All checks passed - Trinity ready to use!"

---

## 📖 Reference for AI

**Must-read docs (for AI to help users):**
- `docs/USER_MANUAL.md` - All commands
- `docs/WHAT_YOU_GET.md` - Benefits explanation
- `docs/INSTALLATION_GUIDE.md` - Full installation options

**Understanding:**
- `docs/ARCHITECTURE_DIAGRAM.md` - How it works
- `MASTER_BLUEPRINT.md` - 3 Locks concept

---

## 🎁 Bonus: One-Liner Installation

AI can offer this to advanced users:

```bash
# One-liner install (for experienced users)
curl -L https://github.com/yourname/trinity/releases/latest/download/install.sh | bash -s -- /path/to/project

# Or:
wget -qO- https://trinity.sh/install | bash -s -- /path/to/project
```

*(Note: Requires hosted installer script)*

---

**For AI Agents:** Follow this guide to help users install Trinity smoothly!

**For Users:** You can ask AI to install Trinity using these instructions.

---

🤖 **AI-Ready Installation Guide**
---

### Appendix A: Trinity Agent Setup (Consolidated)

The agent-specific setup guidance has been consolidated from `.ai/.claude/trinity-agent.md` into a central appendix:

- See: `TRINITY_AGENT_SETUP.md` for quick AI agent workflows, Q&A, and installation scripts.

This reduces duplication and keeps AI-specific instructions current alongside this guide.

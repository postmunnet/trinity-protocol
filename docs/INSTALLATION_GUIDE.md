# Trinity Installation Guide

**How to Use Trinity in a New Project**

---

## 🎯 3 วิธีการติดตั้ง Trinity

### วิธีที่ 1: Copy .ai Folder (แนะนำ - เร็วที่สุด)
### วิธีที่ 2: Git Submodule (สำหรับหลาย projects)
### วิธีที่ 3: Template Repository (สำหรับทีม)

---

## 📦 วิธีที่ 1: Copy .ai Folder (Recommended)

**เหมาะสำหรับ:** Project เดี่ยว, เริ่มใช้เร็ว

### ขั้นตอน (5 นาที)

```bash
# 1. ไปที่ project ใหม่ของคุณ
cd /path/to/your-new-project

# 2. Copy Trinity .ai folder
cp -r /path/to/your/project/.ai .

# 3. ปรับ config
cd .ai
```

แก้ `ssot.yaml`:
```yaml
# เปลี่ยนบรรทัดนี้:
project_root: "/path/to/your/project"

# เป็น:
project_root: "/path/to/your-new-project"
```

```bash
# 4. Setup
bash setup.sh
source .venv/bin/activate

# 5. ทดสอบ
python3 -m cli.main --help
python3 -m cli.main verify selftest

# 6. เริ่มใช้งาน!
python3 -m cli.main session new "First Task"
```

**เสร็จแล้ว!** ⏱️ 5 นาที

---

## 🔗 วิธีที่ 2: Git Submodule

**เหมาะสำหรับ:** หลาย projects ใช้ Trinity ร่วมกัน, update ง่าย

### ขั้นตอน (10 นาที)

```bash
# 1. สร้าง Trinity repository (ครั้งเดียว)
cd /path/to/your/project
git init
git add .ai/
git commit -m "Add Trinity Protocol v0.4"

# Optional: Push to remote
git remote add origin https://github.com/yourname/trinity-protocol.git
git push -u origin main

# 2. ใน project ใหม่ของคุณ
cd /path/to/your-new-project
git init  # ถ้ายังไม่มี

# 3. Add Trinity as submodule
git submodule add https://github.com/yourname/trinity-protocol.git .trinity

# 4. สร้าง symlink
ln -s .trinity/.ai .ai

# 5. Setup
cd .ai
bash setup.sh
source .venv/bin/activate

# 6. ปรับ config
# แก้ .ai/ssot.yaml ให้ project_root ชี้ที่ถูก

# 7. ทดสอบ
python3 -m cli.main verify selftest
```

**ข้อดี:**
- ✅ Update ได้ง่าย (`git submodule update`)
- ✅ ใช้ Trinity เวอร์ชันเดียวกันหลาย projects
- ✅ Track changes ได้

**ข้อเสีย:**
- ⚠️ ซับซ้อนกว่าเล็กน้อย
- ⚠️ ต้องรู้จัก git submodule

---

## 📋 วิธีที่ 3: Template Repository

**เหมาะสำหรับ:** ทีม, organization, หลาย projects

### ขั้นตอน (ครั้งแรก 30 นาที, ต่อไป 2 นาที)

**A. Setup Template (ครั้งเดียว):**

```bash
# 1. สร้าง Trinity template repo
cd /path/to/your/project/.ai
git init
git add .
git commit -m "Trinity Protocol v0.4 Template"

# 2. Push to GitHub
gh repo create trinity-template --public --source=. --remote=origin
git push -u origin main

# 3. สร้าง release
git tag v0.4
git push origin v0.4
```

**B. ใช้ในแต่ละ Project (2 นาที):**

```bash
# 1. ไปที่ project ใหม่
cd /path/to/new-project

# 2. Download Trinity
curl -L https://github.com/yourname/trinity-template/archive/v0.4.tar.gz | tar xz
mv trinity-template-0.4 .ai

# หรือใช้ Git
git clone --depth 1 https://github.com/yourname/trinity-template.git .ai
rm -rf .ai/.git

# 3. ปรับ config
cd .ai
# แก้ ssot.yaml

# 4. Setup
bash setup.sh
source .venv/bin/activate

# 5. เริ่มใช้
python3 -m cli.main session new "First Task"
```

**ข้อดี:**
- ✅ Template มาตรฐานสำหรับทั้งทีม
- ✅ Version control ชัดเจน
- ✅ Update กลางได้ง่าย

---

## 🔧 Configuration Checklist

หลังจาก copy/clone แล้ว ต้องปรับ config:

### 1. แก้ `ssot.yaml` (Required)

```yaml
# File: .ai/ssot.yaml

paths:
  # เปลี่ยนตรงนี้!
  project_root: "/path/to/your-new-project"  # ← Update this!

  # ที่เหลือใช้ default (ไม่ต้องแก้)
  ai_root: "${project_root}/.ai"
  sessions: "${ai_root}/sessions"
  # ...
```

**วิธีง่าย:** ใช้ dynamic detection
```yaml
project_root: "."  # จะ auto-detect จาก cwd
```

---

### 2. ปรับ Deploy Config (Optional)

ถ้าต้องการ deploy จริง:

```yaml
# File: .ai/ssot.yaml

deploy:
  dev:
    type: local_copy  # or rsync, scp
    path: "/path/to/dev/server"

  prod:
    type: rsync
    host: "user@prod-server"
    path: "/var/www/your-app"
    options: "-az --delete --exclude=.git"
```

**ถ้าไม่ต้องการ deploy:**
- เว้นไว้ default (local_copy)
- จะ copy ไปที่ `.ai/deploy/dev/` และ `.ai/deploy/prod/`

---

### 3. ปรับ Safety Rules (Optional)

แก้ `.ai/policies/safety.yaml`:

```yaml
# เพิ่ม forbidden files ของ project คุณ
risk_scoring:
  factors:
    file_types:
      rules:
        - match: "**/*.secrets"     # ถ้า project คุณมี
          score: 100

gates:
  secrets:
    patterns:
      - "(?i)your_api_key[:=]"     # Pattern เฉพาะของคุณ
```

---

## ✅ Post-Installation Checklist

หลังติดตั้งเสร็จ ให้ทดสอบ:

```bash
cd .ai

# 1. Check CLI
python3 -m cli.main --help
✅ Should show commands

# 2. Run selftest
python3 -m cli.main verify selftest
✅ Should pass 3/3 tests

# 3. Create test session
python3 -m cli.main session new "Installation Test"
✅ Should create session structure

# 4. Check status
python3 -m cli.main status show
✅ Should show active session

# 5. Snapshot (if safe)
python3 -m cli.main snapshot run
✅ Should copy files

# 6. Clean up test
python3 -m cli.main close run --force
✅ Should archive
```

**ทั้งหมด PASS:** พร้อมใช้งาน! ✅

---

## 🎓 Project-Specific Customization

### สำหรับ Python Project

```yaml
# ssot.yaml - เพิ่ม:
exclude_patterns:
  - "**/*.pyc"
  - "**/__pycache__"
  - ".venv/"
  - ".pytest_cache/"
```

### สำหรับ Node.js Project

```yaml
exclude_patterns:
  - "node_modules/"
  - "dist/"
  - "build/"
  - ".next/"
```

### สำหรับ PHP Project

```yaml
exclude_patterns:
  - "vendor/"
  - "storage/logs/"
  - "storage/cache/"
```

---

## 🔐 Security Checklist

ก่อนใช้ใน project จริง:

- [ ] Remove test fixtures secrets
  - Check: `tests/verify_fixtures/fail_secret/`
  - ลบ dummy API keys

- [ ] Update .gitignore
  - Add `.ai/sessions/`
  - Add `.ai/archive/`
  - Add `.ai/logs/`
  - Add `.venv/`

- [ ] Review policies
  - Check `policies/safety.yaml`
  - ปรับ forbidden patterns ให้เหมาะกับ project

- [ ] Test verification
  - Run `ai verify selftest`
  - ทดสอบกับ project จริง

---

## 🚀 Quick Setup Script

สร้างไฟล์ `install-trinity.sh`:

```bash
#!/bin/bash
# Quick Trinity Installation Script

set -e

PROJECT_ROOT=$(pwd)
TRINITY_SOURCE="/path/to/your/project/.ai"

echo "🌌 Installing Trinity Protocol..."

# 1. Copy Trinity
if [ -d ".ai" ]; then
    echo "❌ .ai directory already exists"
    exit 1
fi

cp -r "$TRINITY_SOURCE" .ai
echo "✅ Copied Trinity files"

# 2. Update config
cd .ai
sed -i.bak "s|project_root: \".*\"|project_root: \"$PROJECT_ROOT\"|" ssot.yaml
rm ssot.yaml.bak
echo "✅ Updated config"

# 3. Setup
bash setup.sh
echo "✅ Dependencies installed"

# 4. Test
source .venv/bin/activate
python3 -m cli.main verify selftest
echo "✅ Selftest passed"

echo ""
echo "🎉 Trinity installed successfully!"
echo ""
echo "Next steps:"
echo "  1. cd .ai"
echo "  2. source .venv/bin/activate"
echo "  3. python3 -m cli.main session new \"Your First Task\""
```

**ใช้งาน:**
```bash
bash install-trinity.sh
```

---

## 📝 .gitignore Template

เพิ่มใน project root `.gitignore`:

```gitignore
# Trinity Protocol
.ai/sessions/*/DO/dev/*
.ai/sessions/*/DO/prod/*
.ai/sessions/*/DO/snapshot/*
!.ai/sessions/*/.gitkeep

.ai/archive/
.ai/logs/*.log
.ai/state/*.json
.ai/audit/*.ndjson

# Python (if using)
.ai/.venv/
.ai/**/__pycache__/
.ai/**/*.pyc

# Keep structure
!.ai/.gitkeep
!.ai/*/.gitkeep
```

---

## 🔄 Updating Trinity

### ถ้าใช้ Copy Method:

```bash
# 1. Backup config
cp .ai/ssot.yaml /tmp/ssot.yaml.backup

# 2. Copy new version
rm -rf .ai/cli .ai/templates .ai/docs
cp -r /path/to/new-trinity/.ai/cli .ai/
cp -r /path/to/new-trinity/.ai/templates .ai/
cp -r /path/to/new-trinity/.ai/docs .ai/

# 3. Restore config
cp /tmp/ssot.yaml.backup .ai/ssot.yaml

# 4. Update deps
cd .ai
pip install -r requirements.txt --upgrade
```

### ถ้าใช้ Submodule:

```bash
git submodule update --remote
cd .ai
bash setup.sh
```

---

## 🧪 Validation Script

สร้าง `validate-trinity.sh`:

```bash
#!/bin/bash
# Validate Trinity Installation

cd .ai

echo "🔍 Validating Trinity Installation..."
echo ""

# Check Python
if ! python3 --version > /dev/null 2>&1; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✅ Python installed"

# Check dependencies
python3 -c "import typer, rich, yaml" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Dependencies missing - run: bash setup.sh"
    exit 1
fi

# Check CLI
python3 -m cli.main --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ CLI working"
else
    echo "❌ CLI not working"
    exit 1
fi

# Check config
if [ -f "ssot.yaml" ]; then
    echo "✅ Config exists"
else
    echo "❌ ssot.yaml not found"
    exit 1
fi

# Run selftest
python3 -m cli.main verify selftest > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Selftest passed"
else
    echo "⚠️  Selftest failed (check fixtures)"
fi

echo ""
echo "🎉 Trinity validation complete!"
echo ""
echo "Ready to use: python3 -m cli.main session new \"Task\""
```

---

## 📋 Step-by-Step Checklist

### Pre-Installation

- [ ] Have Python 3.8+ installed
- [ ] Have pip installed
- [ ] Have write access to project directory
- [ ] (Optional) Have git initialized

### Installation

- [ ] Copy or clone .ai directory
- [ ] Update `ssot.yaml` with correct `project_root`
- [ ] Run `bash setup.sh`
- [ ] Activate venv: `source .venv/bin/activate`

### Validation

- [ ] Run `python3 -m cli.main --help` (works?)
- [ ] Run `python3 -m cli.main verify selftest` (pass?)
- [ ] Create test session (works?)
- [ ] Check `python3 -m cli.main status show` (displays?)

### Customization

- [ ] Update deploy config (if needed)
- [ ] Update safety rules (if needed)
- [ ] Add project to .gitignore (if using git)
- [ ] Document for team (if team project)

### First Use

- [ ] Create first real session
- [ ] Run snapshot
- [ ] Make small change
- [ ] Run complete workflow
- [ ] Verify it works!

---

## 🎯 Multi-Project Setup

ถ้ามีหลาย projects:

```
~/projects/
├── project-a/
│   └── .ai/           ← Trinity instance 1
├── project-b/
│   └── .ai/           ← Trinity instance 2
└── project-c/
    └── .ai/           ← Trinity instance 3

# หรือใช้ shared Trinity:
~/projects/
├── .trinity/          ← Trinity shared
├── project-a/
│   └── .ai -> ../.trinity/.ai  (symlink)
├── project-b/
│   └── .ai -> ../.trinity/.ai  (symlink)
└── project-c/
    └── .ai -> ../.trinity/.ai  (symlink)
```

**แนะนำ:** แยก instance (วิธีที่ 1) เพราะ:
- Config แยกชัดเจน
- Sessions แยกกัน
- ไม่ conflict

---

## 🔧 Troubleshooting Installation

### Error: "SSOT not found"

**สาเหตุ:** `project_root` ใน ssot.yaml ผิด

**แก้:**
```bash
cd .ai
pwd  # ดู path ที่ถูก
# แก้ ssot.yaml ให้ project_root = parent ของ .ai/
```

---

### Error: "Module not found: typer"

**สาเหตุ:** Dependencies ไม่ได้ติดตั้ง

**แก้:**
```bash
cd .ai
bash setup.sh
source .venv/bin/activate
```

---

### Error: "Selftest failed"

**สาเหตุ:** Fixtures ยังไม่ copy หรือ path ผิด

**แก้:**
```bash
# Check fixtures exist
ls ../tests/verify_fixtures/
# Should show: pass_clean, fail_secret, fail_forbidden

# If not exist, copy from Trinity source:
mkdir -p ../tests
cp -r /path/to/trinity-source/tests/verify_fixtures ../tests/
```

---

## 📦 What to Copy vs What to Customize

### ✅ Copy As-Is (ไม่ต้องแก้)

```
.ai/
├── cli/              ← Copy (code)
├── templates/        ← Copy (templates)
├── policies/         ← Copy (can customize later)
├── schemas/          ← Copy (validation)
├── requirements.txt  ← Copy (deps)
├── setup.sh          ← Copy (installer)
└── .gitignore        ← Copy
```

### 📝 Must Customize

```
.ai/
└── ssot.yaml         ← MUST UPDATE project_root!
```

### 🎨 Optional Customize

```
.ai/
├── policies/safety.yaml   ← Add project-specific rules
└── ssot.yaml             ← Add deploy config
```

### 🗑️ Don't Copy

```
.ai/
├── sessions/     ← Start fresh (empty)
├── archive/      ← Start fresh (empty)
├── logs/         ← Will be generated
└── state/        ← Will be initialized
```

---

## 🎓 Team Installation (Organization)

### สำหรับทีม:

**1. สร้าง Internal Template:**
```bash
# In your org's internal git
git clone https://github.com/yourorg/trinity-template.git
cd trinity-template

# Customize for your org:
# - Update policies/safety.yaml (org standards)
# - Update deploy config (org servers)
# - Add org-specific docs
# - Commit & tag version
```

**2. Team Members ใช้:**
```bash
cd /path/to/their-project
git clone git@internal:yourorg/trinity-template.git .ai
cd .ai
# แก้ ssot.yaml
bash setup.sh
```

**3. Update Mechanism:**
```bash
# In template repo
git pull
git tag v0.5
git push

# Team members
cd .ai
git pull origin main
bash setup.sh  # update deps
```

---

## 📋 Installation Checklist Template

สำหรับแต่ละ project ใหม่:

```markdown
# Trinity Installation - Project: ___________

Date: __________
By: __________

## Checklist

- [ ] Copy .ai folder to project
- [ ] Update ssot.yaml project_root
- [ ] Run setup.sh
- [ ] Activate venv
- [ ] Test CLI (--help)
- [ ] Run selftest (verify selftest)
- [ ] Create test session
- [ ] Snapshot (small test)
- [ ] Verify dev (test gates)
- [ ] Promote (test atomic)
- [ ] Close test session
- [ ] Update .gitignore
- [ ] Document for team (if applicable)
- [ ] ✅ Ready for production use!

## Notes

- Project path: __________
- Python version: __________
- Issues encountered: __________
- Resolution: __________

## First Session

- Date: __________
- Task: __________
- Result: __________
```

---

## 🎁 Bonus: Auto-Install Script

**File:** `auto-install-trinity.sh`

```bash
#!/bin/bash
# Automatic Trinity Installation
# Usage: bash auto-install-trinity.sh [project-path]

PROJECT_PATH="${1:-$(pwd)}"
TRINITY_SOURCE="/path/to/your/project/.ai"

echo "🌌 Trinity Auto-Installer"
echo "========================="
echo ""
echo "Project: $PROJECT_PATH"
echo ""

# Validation
if [ ! -d "$TRINITY_SOURCE" ]; then
    echo "❌ Trinity source not found: $TRINITY_SOURCE"
    exit 1
fi

cd "$PROJECT_PATH" || exit 1

if [ -d ".ai" ]; then
    echo "❌ .ai already exists. Remove it first or use different project."
    exit 1
fi

# Copy
echo "📦 Copying Trinity..."
cp -r "$TRINITY_SOURCE" .ai

# Update config
echo "⚙️  Updating configuration..."
cd .ai
cat > ssot.yaml << EOF
version: "1.0"

paths:
  project_root: "$PROJECT_PATH"
  ai_root: "\${project_root}/.ai"
  policies: "\${ai_root}/policies"
  schemas: "\${ai_root}/schemas"
  templates: "\${ai_root}/templates"
  memory: "\${ai_root}/memory"
  sessions: "\${ai_root}/sessions"
  state: "\${ai_root}/state"
  audit: "\${ai_root}/audit"
  logs: "\${ai_root}/logs"

versions:
  safety_policy: "1.0"
  gates_policy: "1.0"
EOF

# Setup
echo "🔧 Installing dependencies..."
bash setup.sh

# Test
source .venv/bin/activate
python3 -m cli.main --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ CLI working"
else
    echo "❌ CLI test failed"
    exit 1
fi

echo ""
echo "🎉 Installation Complete!"
echo ""
echo "Activate: source .ai/.venv/bin/activate"
echo "Start: python3 -m .ai.cli.main session new \"Task\""
echo ""
echo "📖 Read: .ai/docs/USER_MANUAL.md"
```

**ใช้งาน:**
```bash
# Install in current project
bash auto-install-trinity.sh

# Install in specific project
bash auto-install-trinity.sh /path/to/project
```

---

## 📚 Additional Resources

- **User Manual:** `docs/USER_MANUAL.md`
- **Architecture:** `docs/ARCHITECTURE_DIAGRAM.md`
- **Troubleshooting:** `docs/USER_MANUAL.md` § Troubleshooting

---

## 🆘 Need Help?

**Common Issues:**
- Can't find Python → Install Python 3.8+
- Can't run CLI → Check you're in .ai/ directory
- Selftest fails → Check fixtures at `tests/verify_fixtures/`
- Config errors → Verify ssot.yaml paths

**Support:**
- Read USER_MANUAL.md § Troubleshooting
- Check PRODUCTION_READINESS_CHECKLIST.md
- Review error messages (they're helpful!)

---

**เริ่มต้น:** วิธีที่ 1 (Copy folder) - ง่ายและเร็วที่สุด!

**ขั้นสูง:** วิธีที่ 2-3 เมื่อมีหลาย projects

---

🌌 **Trinity Protocol - Ready for Any Project**

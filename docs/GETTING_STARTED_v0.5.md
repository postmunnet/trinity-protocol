# Getting Started with Trinity Protocol v0.5

**Version:** v0.5 / Phase 6.1 (Agent Sandbox)
**Time to First Session:** 10 minutes
**Difficulty:** Beginner-friendly

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

```bash
# 1. Python 3.8+ installed
python3 --version

# 2. Navigate to Trinity folder
cd /path/to/your/project/.ai

# 3. Setup (first time only - 2 minutes)
bash setup.sh
source .venv/bin/activate

# ✅ Done! Trinity is ready
```

---

## 🎯 Your First Session (5 Minutes)

### Simple Workflow (No Agents)

```bash
# 1. Create session
python3 -m cli.main session new "My First Task"
# ✅ Created: sessions/2025-12-21_my_first_task/

# 2. Backup current state
python3 -m cli.main snapshot run
# ✅ Backed up to DO/snapshot/ and DO/dev/

# 3. Make changes
cd sessions/2025-12-21_my_first_task/DO/dev/
echo "# My changes" > CHANGES.md

# 4. Create simple consensus
cd ../../THINK/
cat > CONSENSUS.md << 'EOF'
# Consensus: My First Task

**Decision:** Add CHANGES.md file
**Rationale:** Testing Trinity workflow
EOF

# 5. Verify and promote
cd ../../../.ai/
python3 -m cli.main verify dev
# ✅ PASS

python3 -m cli.main promote
# ✅ Promoted to prod

python3 -m cli.main verify prod
# ✅ PASS

python3 -m cli.main close run
# ✅ Session closed!

# 🎉 Success! You just completed your first Trinity session!
```

**Time:** ~5 minutes
**Result:** You learned the basic flow!

---

## 🆕 What's New in v0.5? (Agent Sandbox)

### The Power of Multi-Agent Collaboration

**v0.5 adds:**
- 🤖 SANDBOX/ folders (agent workspaces)
- 💬 Debate workflow (reduce bias)
- 🛡️ Enhanced safety (consensus requirement)
- 📊 Separate verify reports (dev/prod)

**Why it matters:**
- Multiple AIs → Better decisions (less bias)
- Parallel work → Faster development
- Human decides → Clear authority
- Safety gates → No mistakes to production

---

## 🤖 Multi-Agent Workflow (10 Minutes)

### Workflow with Debate

```bash
# 1. Create session
cd .ai
python3 -m cli.main session new "Build Authentication System"

# Session created with SANDBOX/gemini|claude|codex/

# 2. Agents work in parallel (you coordinate)
#
# Option A: You write proposals yourself (simulating agents)
# Option B: Use real AI chat to generate proposals
#
# For this example, we'll create simple proposals:

cd sessions/2025-12-21_build_auth/SANDBOX/

# Gemini's proposal (research-based)
cat > gemini/proposal.md << 'EOF'
# Gemini's Proposal: OAuth 2.0

Use industry-standard OAuth 2.0 for authentication.
- Secure by default
- Widely supported
- Token-based (stateless)
EOF

# Claude's proposal (safety-first)
cat > claude/proposal.md << 'EOF'
# Claude's Proposal: Multi-Factor Auth

Add MFA layer to existing auth.
- Backward compatible
- Security enhancement
- Rate limiting included
EOF

# Codex's proposal (implementation-focused)
cat > codex/proposal.md << 'EOF'
# Codex's Proposal: Passkey (WebAuthn)

Modern passwordless authentication.
- No passwords to leak
- Phishing resistant
- Better UX
EOF

# 3. Compile debate
cd ../../../.ai/
python3 -m cli.main debate compile --mode fast

# ✅ Created: SANDBOX/DEBATE/round_1.md (all 3 proposals)
# ✅ Created: SANDBOX/DEBATE/verdict.md (template for you)

# 4. You decide (human authority!)
cd sessions/2025-12-21_build_auth/SANDBOX/DEBATE/
vim verdict.md

# Fill template:
# Decision: Use OAuth 2.0 (Gemini) + MFA (Claude)
# Rationale: Industry standard + security
# Implementation Notes: Codex implements both

# 5. Publish consensus
cd ../../../.ai/
python3 -m cli.main debate publish

# ✅ Validated verdict (no placeholders)
# ✅ Published to THINK/CONSENSUS.md

# 6. Implement (create patch.diff)
cd sessions/2025-12-21_build_auth/SANDBOX/codex/
cat > patch.diff << 'EOF'
--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,5 @@
 def login(user, password):
-    return create_session(user)
+    oauth_token = get_oauth_token(user)
+    mfa_verified = verify_mfa(user)
+    return create_session(user, oauth_token)
EOF

# 7. Apply patch (single ingress!)
cd ../../../.ai/
python3 -m cli.main sandbox apply codex

# ✅ Applied patch to DO/dev/ (atomic, validated)

# 8. Verify and promote
python3 -m cli.main verify dev
# ✅ PASS (no secrets, no forbidden files)

python3 -m cli.main promote
# ✅ PASS (has consensus + verified)

python3 -m cli.main verify prod
# ✅ PASS

python3 -m cli.main close run
# ✅ Session closed!

# 🎉 You just used multi-agent debate!
```

**Time:** ~10 minutes
**Result:** You understand Trinity's power!

---

## 📚 What to Read Next

### After Quick Start:

**Understand the System:**
1. Read `SESSION_CONTRACT.md` (15 min)
   - Complete specification
   - Trust boundaries
   - Safety rules

**Learn Workflows:**
2. Read `docs/USER_GUIDE.md` (30 min)
   - Complete command reference
   - 2 workflow patterns
   - Troubleshooting

**Deep Dive:**
3. Read `MASTER_BLUEPRINT.md` (20 min)
   - Architecture overview
   - The "3 Locks" explained
   - v0.5 hybrid model

---

## 🎯 Common Questions

### Q: ต้องใช้ SANDBOX/ ทุกครั้งไหม?

**A:** ไม่! มี 2 ทางเลือก:

**Simple tasks:** ข้าม SANDBOX/, แก้ในDO/dev/ ตรงๆ
```bash
ai session new "Fix typo"
ai snapshot run
# Edit in DO/dev/
echo "# Fix" > sessions/.../THINK/CONSENSUS.md
ai verify dev → ai promote → ai close
```

**Complex tasks:** ใช้ SANDBOX/ + debate
```bash
ai session new "Major feature"
# Agents work in SANDBOX/
ai debate compile → edit verdict → ai debate publish
ai sandbox apply → ai verify → ai promote
```

---

### Q: CONSENSUS.md จำเป็นจริงๆ ไหม?

**A:** จำเป็น (by default) เพราะ:
- บังคับให้คิดก่อนทำ
- สร้างร่องรอยว่า "ทำไม"
- ป้องกัน cowboy deployment

**แต่:** ถ้าเร่งด่วน ใช้ `--force` ได้ (แต่จะบันทึกไว้)
```bash
ai promote --force  # Emergency only!
```

---

### Q: patch.diff ทำยังไงให้ได้?

**A:** 2 วิธี:

**วิธี 1: Git diff (ง่ายสุด)**
```bash
# ใน SANDBOX/codex/
cp -r ../../DO/dev/* ./temp/
# แก้ไขใน temp/
git diff --no-index ../../DO/dev/ ./temp/ > patch.diff
```

**วิธี 2: diff command**
```bash
diff -u original_file.py modified_file.py > patch.diff
```

**วิธี 3: AI สร้างให้**
```bash
# ใช้ Claude/Codex สร้าง unified diff format
```

---

## ⚡ Pro Tips

### 1. ใช้ `ai status` บ่อยๆ
```bash
python3 -m cli.main status show
# บอกว่าอยู่ที่ไหน ต้องทำอะไรต่อ
```

### 2. ใช้ `ai debate status` ระหว่าง debate
```bash
python3 -m cli.main debate status
# บอกว่า debate ถึงไหนแล้ว
```

### 3. ถ้า lock ค้าง ใช้ `ai unlock`
```bash
python3 -m cli.main unlock
# ปลด .state/LOCK ที่ค้าง
```

### 4. Archive SANDBOX/ เมื่อเสร็จ
```bash
python3 -m cli.main sandbox clean
# Archive SANDBOX/ (ลดขนาด)
```

---

## 🔗 Quick Reference

**Commands You'll Use Most:**
```bash
ai session new "<name>"      # เริ่มงานใหม่
ai snapshot run              # Backup
ai verify dev                # ตรวจสอบ dev
ai promote                   # ปล่อย prod
ai close run                 # ปิดงาน
```

**Debate Commands:**
```bash
ai debate compile --mode fast    # รวบรวม proposals
ai debate publish                # เผยแพร่ verdict
ai debate status                 # ดูสถานะ
```

**Sandbox Commands:**
```bash
ai sandbox apply <agent>     # นำ patch เข้า dev
ai sandbox clean             # เก็บ SANDBOX/
```

---

## 📖 Next Steps

**Just Starting:**
→ Run the "Your First Session" tutorial above

**Want to Learn More:**
→ Read `docs/USER_GUIDE.md`

**Ready to Build:**
→ Read `SESSION_CONTRACT.md` (specifications)

**Need Help:**
→ Check `docs/E2E_TEST_GUIDE.md` (troubleshooting)

---

**🌌 Trinity Protocol v0.5 - You're Ready to Start! 🚀**

**Quick Start:** 5 minutes
**First Session:** 10 minutes
**Master It:** 1 hour

*Stop Chatting. Start Orchestrating.*

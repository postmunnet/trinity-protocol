# Trinity Protocol (Short Readme)

## 1) Opening – What This Is / Isn’t
- ไม่ใช่ multi-agent framework, ไม่ใช่ AI coding IDE
- คือ control plane สำหรับ AI-assisted development ที่ปลอดภัยและมีขั้นตอนชัด
- ใช้โฟลว์แบบมี gate: snapshot → sandbox → verify → promote → deploy

## 2) The Problem (Why)
- AI แก้โค้ดเร็ว แต่ไม่รู้แตะอะไรและย้อนยาก
- Spec ดี แต่ side effects ไม่ถูกกัน
- Chat workflow ไม่มี audit / rollback ที่มั่นใจ
- Multi-agent มักพังเพราะ context แตก

## 3) The Idea (What Trinity Does)
- Session-based: ทุกงานอยู่ใน session เดียวกัน
- Snapshot ก่อนแก้เสมอ (ย้อนง่าย)
- Sandbox สำหรับ AI/มนุษย์แยกจากต้นฉบับ
- Verify → Promote → Deploy มี gate/checklist
- Artifact-first: diff, logs, state, reports เก็บครบ

## 4) 5-Minute Quick Start
```bash
cd .ai
python3 -m cli.main session new "My Task"
python3 -m cli.main snapshot run
# ให้ AI/คุณแก้ที่ sessions/<id>/DO/dev
python3 -m cli.main verify dev
python3 -m cli.main promote
python3 -m cli.main deploy dev   # ถ้าต้องการ
```

## 5) When to Use / Not Use
- ใช้เมื่อ: แก้ระบบบ่อย, ใช้ AI หนัก, ต้อง rollback/audit, มีหลาย agent/iteration
- ไม่ใช้เมื่อ: งานเล็กครั้งเดียว, chat แก้โค้ดธรรมดาพอ, ไม่สน audit/rollback

## 6) Links
- User Guide (5 นาทีลงมือ): `.ai/docs/USER_GUIDE.md`
- Architecture: `.ai/MASTER_BLUEPRINT.md`
- Contributing: `.ai/CONTRIBUTING.md`


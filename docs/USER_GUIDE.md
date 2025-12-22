# Trinity Protocol – User Guide (5 นาทีใช้งานได้จริง)

เวอร์ชันย่อ เน้นทำงานจริง ไม่ลงปรัชญา

## 1) What Trinity Is
- Control plane สำหรับ AI-assisted coding
- Session-based, local-first, มี gate (snapshot → verify → promote → deploy)
- ปลอดภัยกว่าการให้ AI แก้โค้ดตรง ๆ เพราะมี sandbox + audit

## 2) Core Concepts (ศัพท์ให้ตรงกัน)
- Session: พื้นที่งานหนึ่งงาน (โฟลเดอร์ sessions/<id>)
- Snapshot: ก๊อปสถานะปัจจุบันไป DO/snapshot แล้วสร้าง DO/dev ไว้แก้
- Workspace/Sandbox: ที่ให้ AI/มนุษย์แก้ (DO/dev หรือ SANDBOX/*)
- Verify: รัน gate (forbidden/secret/smoke) ก่อนเลื่อนขั้น
- Promote: ย้าย dev → prod (ต้อง verify dev ผ่าน)

## 3) Daily Workflow (ตัวอย่าง feature/bug รายวัน)
```bash
cd .ai
python3 -m cli.main session new "Fix login rate limit"   # สร้าง session
python3 -m cli.main snapshot run                        # backup + สร้าง DO/dev
# แก้โค้ดใน sessions/<id>/DO/dev หรือใช้ SANDBOX/patch แล้ว apply
python3 -m cli.main verify dev                          # gate ก่อนเลื่อน
python3 -m cli.main promote                             # dev → prod
python3 -m cli.main verify prod                         # ยืนยัน prod
python3 -m cli.main deploy dev                          # ถ้าต้องการ deploy dev
python3 -m cli.main close run                           # ปิด session เมื่อจบ
```
Rollback: ใช้ snapshot/DO/snapshot เป็นจุดย้อนกลับ หรือ discard session แล้วสร้างใหม่

## 4) Using Multi-Agent (เลือกแบบใดแบบหนึ่ง)
- Mode A: Single Writer — ให้ AI/มนุษย์ 1 ตัวเขียน, ที่เหลือ review/verify
- Mode B: Parallel Sandbox — แต่ละ agent แก้ใน SANDBOX ของตัวเอง → เลือก patch มารวมทีหลัง
แนวทาง: เริ่มที่ Single Writer เป็นค่า default; ใช้ sandbox แยกถ้าต้องการลองหลายแนว

## 5) Common Mistakes
- ไม่ snapshot ก่อนแก้ → rollback ยุ่งยาก
- ให้หลาย agent เขียน DO/dev พร้อมกัน → diff ปะปน
- เชื่อ chat มากกว่าดู diff/verify
- ปล่อย patch ที่แตะ SSOT/schemas โดยไม่มี scope guard

## 6) Troubleshooting (เร็ว)
- verify dev/prod fail → อ่านรายงานใน `.state/verify_dev.json` / `.state/verify_prod.json`
- deploy ไม่ออก → DO/dev หรือ DO/prod ต้องมี real content (ไม่ใช่แค่ `.gitkeep`)
- lock ค้าง → `python3 -m cli.main unlock run --force`
- selftest → `python3 -m cli.main verify selftest` (auto-gen fixtures แล้ว)

## 7) Reference Commands (จำแค่ชุดนี้)
- `ai session new "<task>"` — สร้าง session
- `ai snapshot run` — backup → DO/snapshot → DO/dev (preflight verify)
- `ai sandbox apply --path <patch>` — apply diff แบบมี guard
- `ai verify dev|prod` — gate ก่อน promote/close
- `ai promote` — dev → prod (ต้อง verify dev ผ่าน)
- `ai deploy dev|prod` — deploy จาก DO/dev หรือ DO/prod (ตรวจ real content)
- `ai close run` — ปิด session (ต้อง verify prod)
- `ai unlock run` — ล้าง lock
- `ai vault ...` — จัดการ secrets

## 8) เพิ่มเติม (ถ้าต้องรู้ลึก)
- Architecture: `../MASTER_BLUEPRINT.md`
- Quick start: `PHASE6_QUICKSTART.md`
- Secrets vault: `SECRETS_GUIDE.md`
- GitHub usage: `GITHUB_GUIDE.md`
- Install: `INSTALLATION_GUIDE.md`

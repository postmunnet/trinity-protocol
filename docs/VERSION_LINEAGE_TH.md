# Version Lineage (ไทย)

ภาษา: [English](VERSION_LINEAGE.md) | ไทย

Trinity แยก version line ของ architecture, runtime และ tool contract ออกจากกัน
ไม่ควรเอาทุกอย่างไปรวมเป็นเลขเดียว

```text
Trinity Protocol v2  = architecture / constitution generation
Runtime v0.1.0       = first public executable runtime line
Tool Contract        = v1.0 freeze candidate, v1.1 draft working spec
```

## v0.1.0

Trinity v0.1.0 คือ public runtime line แรกที่พร้อมใช้สำหรับ repository
`trinity_v2`

repository นี้เคยมีวัสดุทดลองของ Trinity Protocol รุ่นก่อนหน้าอยู่ก่อนแล้ว
ตั้งแต่ `v0.1.0` เป็นต้นไป root tree นี้ถือเป็น canonical Trinity v2
executable governance kernel ส่วน legacy materials ยังดูย้อนหลังได้จาก Git
history

Release evidence:

- [`docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`](releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md)

คำสั่งที่ใช้ verify:

```bash
python3 -m pytest .ai/cli/tests -q
```

ผลที่ verify แล้ว:

```text
Source checkout: 1862 passed, 6 skipped
Clean export without optional sibling tools: 1860 passed, 8 skipped
```

## Lineage

- Source family: บทเรียนจาก `TRINITY_LEGACY` kernel และ migration evidence
- Current repo: `trinity_v2`, clean public bootstrap/runtime target
- Public export: สร้างด้วย `scripts/export_github.sh` และ
  `scripts/package_github_zip.sh`

## Release Discipline

Stable tag ต้องชี้ไปที่ commit ที่ผ่าน verification จริง ห้าม tag dirty
worktree และห้าม tag commit เก่าด้วย evidence จากไฟล์ใหม่

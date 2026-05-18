# ทำไมต้องมี Trinity?

ภาษา: [English](WHY_TRINITY.md) | ไทย

AI coding agent เก่งขึ้นมาก แต่คำพูดของมันยังไม่ใช่หลักฐาน

มันสามารถบอกว่า "เสร็จแล้ว" ได้ โดยที่ยังไม่มีอะไรพิสูจน์ว่างานเสร็จจริง

ตัวอย่างปัญหา:

- บอกว่า test ผ่าน แต่ไม่มี test artifact
- บอกว่า bug แก้แล้ว แต่ไม่มี reproduction ที่ verify แล้ว
- บอกว่า deploy ปลอดภัย แต่ไม่มี rollback path
- บอกว่าแก้ไฟล์ถูกแล้ว แต่ยังไม่มี diff ให้ตรวจ

Trinity ถูกสร้างมาเพื่อเปลี่ยนงานที่ใช้ AI ให้เป็น evidence-driven workflow

---

## ก่อนมี Trinity

```text
User: แก้ login bug ให้หน่อย
Agent: เสร็จแล้วครับ test ผ่านแล้ว
```

ปัญหาไม่ใช่ว่า agent ต้องผิดเสมอ

ปัญหาคือคำพูดนั้นยังไม่พอ

ยังไม่มีหลักฐานที่ตรวจได้:

- ไม่มี scoped plan
- ไม่มี diff summary
- ไม่มี test log
- ไม่มี verifier verdict
- ไม่มี audit event
- ไม่มี promotion decision

---

## หลังมี Trinity

```text
User: แก้ login bug ให้หน่อย
Trinity:
1. บังคับให้มี plan artifact ที่ระบุ scope
2. อนุญาตให้ execute เฉพาะใน boundary ที่ผ่าน gate
3. เก็บ diff, log, test output, screenshot หรือ evidence อื่น
4. ให้ verifier ตรวจหลักฐาน
5. อนุญาตให้ promote เฉพาะเมื่อ evidence ผ่าน
```

ถ้าไม่มี artifact ก็ยังเชื่อไม่ได้

ถ้า verification ไม่ผ่าน ก็ยังถือว่างานไม่เสร็จ

ถ้าไม่มี authority ที่ถูกต้อง ก็ห้ามข้าม state

---

## หลักการหลัก

```text
Trust artifacts, not claims.
```

AI agent เสนอได้ ลงมือได้ใน scope ที่กำหนดได้ และเขียน artifact ได้

แต่ไม่ควรเป็นผู้ตัดสินสุดท้ายว่างานของตัวเองเสร็จแล้ว

Trinity ใช้ลำดับการตัดสินแบบนี้:

```text
Deterministic verifier
    -> Policy / rules
    -> LLM judge เฉพาะเมื่อถูก gate
    -> Human authority
```

---

## Trinity คืออะไร

Trinity คือ control layer แบบ CLI-first สำหรับ AI coding agent

มันประสาน vendor AI harness, ตรวจงานจากหลักฐาน, และบันทึก decision เป็น
auditable artifact

มันเหมาะกับ developer หรือ technical operator ที่ใช้ Claude Code, Codex,
Cursor หรือ Gemini อยู่แล้ว แต่ไม่อยากเชื่อคำกล่าวอ้างของ agent โดยไม่มี evidence

---

## Trinity ไม่ใช่อะไร

Trinity ไม่ใช่:

- chatbot อีกตัว
- agent framework ทั่วไป
- MCP-first tool registry
- memory app
- generic orchestrator
- ตัวแทนของ vendor AI harness

Trinity คือ control plane ระหว่าง human intent กับ AI execution

---

## สรุปสั้นที่สุด

Trinity ไม่ได้ทำให้ AI เก่งขึ้น

Trinity ทำให้งานของ AI ตรวจสอบและรับผิดชอบได้

```text
ไม่มี artifact = ยังเชื่อไม่ได้
ไม่มี verification = ยังถือว่างานไม่เสร็จ
ไม่มี authority = ห้ามข้าม state
```

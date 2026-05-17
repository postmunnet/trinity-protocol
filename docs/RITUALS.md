# Trinity Rituals — Operator Reference

เอกสารนี้เป็น operator-facing reference สำหรับ ritual ทั้ง 7 ตัวใน Trinity

อ่านแบบเล่าที่มาเหตุผลว่าทำไม Trinity ถึงเลือกแนวนี้ ดูได้ที่
[`ORIGIN.md`](ORIGIN.md)

รายละเอียดเชิง contract แบบ technical (state machine, schema, audit format)
อยู่ใน [`constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md)
และ specs ที่เกี่ยวข้องใต้ [`specs/`](specs/)

---

## Quick Reference

| Ritual | ใช้เมื่อ | หน้าที่หลัก |
|---|---|---|
| `sss` | ก่อนเริ่ม session | สร้าง session capsule + snapshot state ตั้งต้น |
| `vvv` | ก่อน plan/execute | นิยาม goal / scope / constraint / acceptance / risk |
| `nnn` | หลัง vvv ผ่าน | แปลง goal เป็น plan + step + expected artifact |
| `gogogo` | หลัง plan ผ่าน | explicit execution gate — อนุญาตให้ลงมือ |
| `ddd` | หลัง execute | ตรวจ diff / damage / scope creep จากของจริง |
| `rrr` | หลังจบงาน หรือเจอ failure | เปลี่ยนประสบการณ์เป็นบทเรียน (retro) |
| `close` | จบ session | ปิด session อย่างมีสถานะชัดเจน |

ลำดับมาตรฐาน: `sss` → `vvv` → `nnn` → `gogogo` → `ddd` → `rrr` → `close`

---

## `sss` — Session Capsule / Snapshot / Starting State

ใช้ก่อนเริ่มงานสำคัญ

หน้าที่ของ `sss` คือสร้าง session capsule และเก็บสถานะตั้งต้นก่อนเริ่มลงมือ

มันช่วยตอบคำถามว่า:

- ตอนเริ่มงาน state เป็นอย่างไร
- มีไฟล์สำคัญอะไรบ้าง
- context ที่ต้องรู้คืออะไร
- ถ้าทำพังจะย้อนกลับไปจุดไหน
- session นี้กำลังแก้เรื่องอะไร

`sss` ทำให้การเริ่มงานไม่ใช่การกระโดดเข้าไปแก้ทันที
แต่เริ่มจากการสร้างจุดอ้างอิงก่อน

---

## `vvv` — Goal / Scope / Constraint / Acceptance / Risk

ใช้เป็น gate ก่อน planning หรือ execution

`vvv` บังคับให้ต้องตอบ 5 คำถามหลัก:

1. **Goal** — งานนี้สำเร็จหน้าตาเป็นอย่างไร
2. **Scope** — อะไรอยู่ในขอบเขต และอะไรอยู่นอกขอบเขต
3. **Constraint** — อะไรห้ามแตะ ห้ามทำ หรือห้ามเปลี่ยน
4. **Acceptance** — จะรู้ได้อย่างไรว่างานเสร็จจริง
5. **Risk** — failure mode ที่น่ากลัวที่สุดคืออะไร

สิ่งนี้สำคัญมาก เพราะปัญหาใหญ่ของ AI คือมันมักลงมือก่อนเข้าใจขอบเขต

`vvv` ทำให้ก่อนจะเริ่มงาน ต้องนิยามสนามให้ชัดก่อน

---

## `nnn` — Normalize / Plan / Next Action

ใช้เพื่อจัดรูปงานให้เป็นแผนที่ทำได้จริง

หลังจากรู้ goal และ scope แล้ว `nnn` ช่วยแปลงงานให้เป็น:

- plan
- step
- dependency
- expected artifact
- verification path
- next action

เป้าหมายของ `nnn` ไม่ใช่ให้ AI คิดเยอะเฉย ๆ
แต่ให้มันสร้างแผนที่ตรวจสอบได้ก่อน execute

---

## `gogogo` — Explicit Execution Gate

ใช้เป็นสัญญาณว่าอนุญาตให้ลงมือได้

ก่อนมี gate นี้ ปัญหาที่เจอบ่อยคือ AI ชอบเริ่มแก้เองทันที
ทั้งที่ผมยังแค่ถามหรือกำลัง brainstorm

`gogogo` เลยกลายเป็นเส้นแบ่งชัดเจนระหว่าง:

- กำลังคิด
- กำลังวางแผน
- กับ "อนุญาตให้ execute แล้ว"

หลักการคือ:

> ถ้ายังไม่มี explicit execution gate
> อย่าทำ action ที่เปลี่ยน state สำคัญ

---

## `ddd` — Diff / Inspect / Damage Check

ใช้หลัง execute เพื่อดูว่าเปลี่ยนอะไรจริง

ปัญหาหนึ่งของ AI คือมันมักอธิบายว่าแก้อะไรไป
แต่สิ่งที่มันพูดอาจไม่ตรงกับสิ่งที่เกิดขึ้นจริงในไฟล์

`ddd` จึงเน้นตรวจจากของจริง:

- diff คืออะไร
- ไฟล์ไหนถูกแก้
- มีไฟล์ที่ไม่ควรถูกแตะไหม
- scope creep เกิดขึ้นไหม
- change ตรงกับ plan หรือไม่
- มี damage ที่ต้อง rollback ไหม

`ddd` คือ ritual ที่ย้ำว่า:

> อย่าเชื่อคำอธิบายก่อนเห็น diff

---

## `rrr` — Retro / Lesson / Memory

ใช้หลังจบงานหรือหลังเจอ failure

หน้าที่ของ `rrr` คือเปลี่ยนประสบการณ์ให้กลายเป็นบทเรียน

ไม่ใช่แค่สรุปว่างานเสร็จ
แต่ต้องตอบว่า:

- เกิดอะไรขึ้น
- อะไรทำให้สำเร็จ
- อะไรเกือบพัง
- มี pattern อะไรที่ควรจำ
- ครั้งหน้าควรทำอะไรต่างออกไป
- ควรเพิ่ม rule หรือ verifier อะไรไหม

`rrr` คือสะพานจากงานหนึ่งไปสู่งานถัดไป
ทำให้ session ไม่หายไปเฉย ๆ หลังปิด chat

---

## `close` — Close Session / Final State

ใช้ปิด session อย่างมีสถานะ

ก่อนมี `close` หลาย session จบแบบลอย ๆ:

- ไม่รู้ว่างานจบจริงไหม
- ไม่รู้ว่า test ผ่านหรือยัง
- ไม่รู้ว่ามี artifact ไหนสำคัญ
- ไม่รู้ว่าต้องทำอะไรต่อ
- ไม่รู้ว่ายังมี risk ค้างไหม

`close` ทำให้ session ต้องมี final state:

- done หรือ not done
- artifact อยู่ไหน
- verify ผ่านไหม
- มี pending issue อะไร
- next step คืออะไร
- มีอะไรต้องจำเข้า retro หรือ memory ไหม

จากตรงนี้ session ไม่ใช่แค่บทสนทนา
แต่กลายเป็นหน่วยงานที่ปิดบัญชีได้

---

## See Also

- [`ORIGIN.md`](ORIGIN.md) — ที่มาและเหตุผลเบื้องหลัง ritual ทั้งหมด
- [`constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md`](constitution/contracts/TRINITY_RITUAL_CONTRACT_V1.md) — canonical contract
- [`operator-guide-th/03_RITUAL_LOOP.md`](operator-guide-th/03_RITUAL_LOOP.md) — คู่มือใช้งาน ritual loop (ไทย)
- [`operator-guide-en/03_RITUAL_LOOP.md`](operator-guide-en/03_RITUAL_LOOP.md) — ritual loop operator guide (English)
- [`specs/INDEX.md`](specs/INDEX.md) — master spec index

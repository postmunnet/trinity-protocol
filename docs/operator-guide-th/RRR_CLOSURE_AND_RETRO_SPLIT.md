---
title: "การปิด rrr และการแยก Retro"
audience: "Operator (มนุษย์ + AI agent)"
last-updated: "2026-05-24"
---

# การปิด rrr และการแยก Retro

`rrr` คือ **terminal closure organ** ของ Trinity session ไม่ใช่ขั้นตอน
"reflection" มันไม่เขียน lessons มันไม่ pin doctrine สิ่งที่มันทำคือ
งานเชิงกลไกที่มีขอบเขตชัดเจน

ส่วนการสะท้อนเชิงความหมาย — "อะไรเวิร์ก / อะไรพัง / เราเรียนรู้อะไร" —
เป็น **organ คนละตัว** บทนี้อธิบายการแยกนั้น, artifact สี่ชิ้นที่
เกี่ยวข้อง (สามชิ้นบังคับ + หนึ่งชิ้น optional), และ playbook ที่
operator ใช้ทำงานกับมัน

Spec ที่เป็น canonical (อ่านอันนี้ถ้ามีจุดไหนคลุมเครือ):
[`docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](../specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md)

## `rrr` ทำอะไรบ้างจริง ๆ

เมื่อรัน `bash .ai/cli/ai rrr` kernel จะทำงาน deterministic สามอย่าง
กับ session ที่ active แล้วเขียน artifact canonical หนึ่งไฟล์

```text
1. Acceptance evidence
   - อ่าน THINK/03_ACCEPTANCE.yaml
   - รันคำสั่ง A* แต่ละข้อใน /bin/sh
   - บันทึก actual_exit เทียบกับ expect_exit ของแต่ละ criterion

2. Forbidden-diff
   - เทียบ working tree กับ baseline_untracked (snapshot ตอน sss)
   - ปฏิเสธการเขียนนอก allowed_paths ของ plan
   - ปฏิเสธการเขียนใส่ .ai/policies/** และ .ai/audit/** (การ mutate)

3. Transition + chain accounting
   - นับ graph.transition events ของ session
   - รวม verdict ของ gogogo (pass / fail / unverified / retry / needs_human)
   - Anchor audit chain head + last_seq ของ session
```

ผลลัพธ์ทั้งสามอย่างนั้นถูกบันทึกเป็นไฟล์ closure record ไฟล์เดียว ไม่มี
prose ไม่มีความเห็น ไม่มี "session ครั้งนี้ผ่านไปด้วยดี"

## ทำไมต้องแยก

มีสองมาตราในรัฐธรรมนูญที่บังคับการแยกนี้

**Article IX — Memory Discipline** เขียนไว้ตรง ๆ ว่า

```text
Memory retrieves evidence.
It does not govern meaning.
```

ถ้า `rrr` เขียน lessons แปลว่า `rrr` กำลัง govern meaning นั่นคือการ
ละเมิด Article IX ที่ `rrr.py` legacy แบกอยู่หลายเดือน Phase 12 แก้
ด้วยการตัดการสังเคราะห์เชิงความหมายออกจาก closure path ทั้งหมด

**Article IV — Separation of Responsibilities** มอบหน้าที่ post-work
reflection ให้ `Retro` organ ไม่ใช่ `Kernel` `rrr` เป็น kernel command
ถ้า kernel command มาเขียน reflection ด้วย คือ role collapse แบบ
ตำราเรียน

Boundary contract (spec §2.3) มีแค่สี่บรรทัด:

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```

ถ้าบรรทัดไหนหยุดเป็นจริง สิ่งที่คุณมีในมือไม่ใช่ refactor แต่เป็นการ
ขอแก้รัฐธรรมนูญ

## Artifact สี่ชิ้น

สามชิ้นถูกเขียนทุกครั้งที่รัน `rrr` ส่วนชิ้นที่สี่ — `RETRO_LESSONS.md`
— เป็น **optional** จะปรากฏก็ต่อเมื่อ operator ส่ง `--with-lessons` เท่านั้น

| # | Artifact | Schema | ผู้เขียน | Trigger | กลไก / ความหมาย | อยู่ที่ |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `retro_envelope.md` | `trinity.retro_envelope.v1` (13 fields, frozen) | `rrr` (kernel) | ทุกครั้งที่รัน `rrr` | กลไก | `<session>/THINK/retro_envelope.md` |
| 2 | `RETRO.md` | `trinity.retro_md.v1` | `rrr` (kernel) | ทุกครั้งที่รัน `rrr` | กลไก (header render มาจากข้อมูล envelope) | `<session>/THINK/RETRO.md` |
| 3 | **`RETRO_LESSONS.md`** | ไม่มี (free-form markdown) | kernel เขียนไฟล์จาก stdout ของ agent `retro_writer` | **OPTIONAL — เฉพาะเมื่อรัน `bash .ai/cli/ai rrr --with-lessons`** | เชิงความหมาย (proposal-only) | `<session>/THINK/RETRO_LESSONS.md` |
| 4 | สำเนา retro ที่ถูก index | mirror ของ `RETRO.md` | `rrr` copy + `memory-cli index` อ่าน | ทุกครั้งที่รัน `rrr` | กลไก | `.ai/memory/retros/NNNN_<ts>_<slug>.md` |

### 1. `retro_envelope.md` — closure record เชิงกลไก

ไฟล์นี้คือ closure record frontmatter ของมันถูก freeze ที่ 13 fields พอดี
ตาม `RRR_OUTPUT_FIELDS` ใน `.ai/cli/core/retro_rrr_contract.py`:

```text
session_id            ts_started        ts_closed
duration_seconds      acceptance_results
forbidden_diff_status baseline_untracked
audit_chain_status    transition_count  gogogo_verdicts
tier                  memory_index_result
artifact_paths
```

Consumer ปลายทาง — `presentation_renderer`, `close`, ตัวสร้าง DDD packet
— อ่านไฟล์นี้เป็น source of truth ของ "มีอะไรเกิดขึ้นเชิงกลไกใน session
นี้" พวกมันไม่ parse `RETRO.md` การเพิ่ม field เข้า envelope ต้องผ่าน
Article XXIX amendment

### 2. `RETRO.md` — บันทึกเชิงกลไกของ kernel (กระจกเงาที่มนุษย์อ่านได้ของ envelope)

`rrr` เขียน `RETRO.md` เสมอจากฝั่ง kernel เนื้อหาเป็น **เชิงกลไกล้วน**:
ข้อมูลชุดเดียวกับ `retro_envelope.md` (acceptance / forbidden-diff /
transition) แต่ render เป็น prose ให้มนุษย์อ่านได้โดยไม่ต้อง parse
frontmatter เอง `rrr` ไม่เขียน prose ประเภท "Lessons" / "What worked"
ลงในไฟล์นี้ — เนื้อหา semantic ประเภทนั้นอยู่ใน `RETRO_LESSONS.md`
(artifact #3, optional)

### 3. `RETRO_LESSONS.md` — proposal เชิงความหมายจาก `retro_writer` (optional)

ไฟล์นี้จะถูกเขียน **เฉพาะเมื่อ** operator ส่ง `--with-lessons` บนคำสั่ง
`rrr` เมื่อมี flag นี้ kernel จะ shell ออกไปเรียก in-house agent
`retro_writer` แล้วเขียน stdout ของ agent ลงใน
`<session>/THINK/RETRO_LESSONS.md` แบบ verbatim agent ตัวนี้ **ห้าม**
ไปแก้ `RETRO.md` (contract ของ agent บังคับเอง) `RETRO_LESSONS.md`
จึงเป็นไฟล์ข้างเคียงเสมอ ไม่ใช่การเขียนทับ

```bash
# Retro เชิงกลไกล้วน (default — RETRO_LESSONS.md จะไม่ถูกสร้าง)
bash .ai/cli/ai rrr

# Retro เชิงกลไก + ไฟล์ข้างเคียงเชิงความหมายจาก retro_writer
bash .ai/cli/ai rrr --with-lessons
```

`retro_writer` เป็น **proposal-only** operator ต้องตรวจ
`RETRO_LESSONS.md` ก่อนถึงจะถือว่าเป็น reflection of record ของ session
ถ้า proposal ผิด แก้ด้วยมือ — agent ไม่มี authority ถ้า agent timeout
หรือ stdout ว่าง kernel จะ print warning สีเหลืองแล้ว skip ไฟล์ ส่วน
`rrr` ที่เหลือยังรันจบเรียบร้อย

### 4. `.ai/memory/retros/NNNN_*.md` — index ไว้สำหรับ recall ข้าม session

หลังเขียน `RETRO.md` เสร็จ `rrr` คัดลอกไฟล์ไปไว้ใต้
`.ai/memory/retros/` โดยใช้ชื่อลำดับถัดไป `NNNN_<ts>_<slug>.md` แล้ว
delegate ให้ `memory-cli index` ทำให้สืบค้นได้จาก session ถัดไป
Envelope ที่ได้จากการ delegate ถูก capture verbatim เข้าไปใน
`retro_envelope.md` ใต้คีย์ `memory_index_result` — `rrr` ไม่ตีความ
ไม่สรุป ไม่กรอง

สำเนาที่ index ไว้คือการเก็บ evidence ไม่ใช่ doctrine มัน search ได้
ผ่าน `memory-cli search` แต่ **ไม่ใช่** canonical จนกว่ามนุษย์จะ pin
(ดู playbook ด้านล่าง)

## Operator Playbook

### เมื่อ `rrr` fail ที่ acceptance

อ่าน `RETRO.md` ส่วน "Acceptance evidence" จะ list คำสั่ง A* แต่ละข้อ
พร้อม expected vs actual exit code สามจุดที่พบบ่อย:

```text
1. คำสั่งใช้ bash syntax แต่ /bin/sh ไม่รองรับ
   อาการ: A* fail พร้อม "syntax error" หรือ "[[: not found"
   วิธีแก้: เขียนใหม่ในรูป POSIX sh; arrays / [[ ]] / <(...) ไม่ portable
   (ดู memory feedback_acceptance_command_sh_vs_bash)

2. grep -F pattern มี curly quote / em-dash / nbsp ติดมาจากการ copy-paste
   อาการ: A* fail เงียบ ๆ ด้วย exit 1 ทั้งที่เห็นด้วยตาว่า substring
   "มีอยู่ใน" ไฟล์
   วิธีแก้: copy substring จากไฟล์ปลายทางตรง ๆ แล้วอัปเดต **ทั้งสอง**
   ไฟล์ คือ THINK/03_ACCEPTANCE.yaml และ .state/plan.json
   (ดู memory feedback_acceptance_grep_char_mismatch)

3. Plan ลิสต์ child file แต่ลืม parent file ใน allowed_paths
   อาการ: A* พยายาม verify การแก้ที่ forbidden-diff ปฏิเสธไป
   วิธีแก้: แก้ plan ให้รวม parent ด้วย (เช่นต้องมี audit.py เมื่อเพิ่ม
   subcommand audit_<sub>.py)
   (ดู memory feedback_typer_subcommand_needs_parent_in_allowed_paths)
```

แก้แล้วรัน `bash .ai/cli/ai rrr` ใหม่ มัน idempotent ถ้า input เหมือนเดิม

### เมื่อต้องการไฟล์ข้างเคียงเชิงความหมาย (`--with-lessons`)

โดย default `rrr` เขียนเฉพาะ artifact เชิงกลไก (#1, #2, #4) ถ้าต้องการให้
สร้าง `RETRO_LESSONS.md` ด้วย (artifact #3 — proposal เชิงความหมายจาก
`retro_writer`) ต้องส่ง flag เปิดอย่างชัดเจน:

```bash
bash .ai/cli/ai rrr --with-lessons
```

kernel จะ shell ออกไปเรียก in-house agent ที่
`.ai/cli/agents/retro_writer/` จับ stdout ของมัน แล้วเขียนไฟล์ที่
`<session>/THINK/RETRO_LESSONS.md` พฤติกรรมที่ต้องคาด:

```text
- Agent รันด้วย timeout 120 วินาที
- ถ้า exit ไม่เป็นศูนย์ หรือ stdout ว่าง: kernel จะ print warning
  สีเหลืองแล้ว skip ไฟล์ rrr ทั้ง run ยังจบสำเร็จตามปกติ
- Agent **ห้าม** ไปแก้ RETRO.md — RETRO_LESSONS.md เป็นไฟล์แยกเสมอ
- ไฟล์นี้คือ proposal เท่านั้น ต้องอ่าน ต้องตรวจ ห้ามถือ prose ของ
  agent เป็น authority
```

ถ้ารัน `rrr --with-lessons` ซ้ำใน session เดิม ไฟล์จะถูกเขียนทับด้วย
stdout ล่าสุดของ agent ไม่มีโหมด append

### เมื่อ `close` ติด gate-lock หลัง `rrr` ผ่าน

`close` ต้องการให้ verification **ทั้งสอง** stream ผ่านเขียวก่อนถึงจะยอม
archive session:

```bash
bash .ai/cli/ai verify dev
bash .ai/cli/ai verify prod
```

ข้อความ error เดิมเอ่ยถึงแค่ `prod` แต่จริง ๆ ต้องมี dev ด้วย ถ้าตัวใด
ตัวหนึ่งหายหรือแดง `close` จะปฏิเสธพร้อม gate-lock รันให้ครบทั้งคู่
ยืนยันว่า PASS ทั้งสองแล้วค่อยลอง `close` อีกครั้ง

### Pin retro เป็น canonical doctrine (เฉพาะมนุษย์)

ถ้า retro ไหนเก็บ pattern ที่อยากให้ session ในอนาคต cite ถึง **คุณ**
เป็นคน pin ไม่ใช่ `rrr` ไม่ใช่ `retro_writer` ไม่ใช่ agent ตัวไหน

```bash
memory-cli pin .ai/memory/retros/0123_2026-05-24_my-task.md \
              --as=retro-my-task \
              --reason='canonical pattern for X'
```

`--reason` บังคับต้องมี เหตุผลว่างคือการละเมิดรัฐธรรมนูญ (Article XIII
สงวน irreversible action ไว้ให้ human authority อย่างชัดเจน) Event ที่
เกิดจากการ pin จะถูก audit เป็น `decided_by: human`

`rrr` อาจ print suggestion ทาง stdout ให้ pin ได้ในกรณีที่ session มี
transition `decided_by: human` แต่ข้อความนั้นเป็นความเอื้อเฟื้อ ไม่ใช่
การตัดสิน การ auto-pin / auto-promote / kernel-side pin emission ถูก
ห้ามทั้งหมด

## สิ่งที่ `rrr` **ห้ามทำ** (Forbidden Patterns)

ตาม spec §3.2 source ของ `rrr.py` ห้ามมีสตริงต่อไปนี้:

```text
memory-cli learn
learn --file=
"memory_learn"
'memory_learn'
call_tool(..., "memory-cli", "pin ...")
call_tool(..., "memory-cli", "promote ...")
call_tool(..., "memory-cli", "verify ...")
call_tool(..., "memory-cli", "trace ...")
call_tool(..., "memory-cli", "embed ...")
call_tool(..., "memory-cli", "similar ...")
```

มี source-level lint บังคับเรื่องนี้ verb เดียวของ `memory-cli` ที่
`rrr` เรียกได้คือ `index` เพราะการ index คือการเก็บ evidence เชิงกลไก
verb อื่น ๆ ล้วนเป็น semantic (`learn`, `verify`, `embed`, `similar`)
หรือถือ authority (`pin`, `promote`) จึงอยู่นอกขอบเขต authority ของ
`rrr` (Article XVI — Least Authority)

`rrr` ยังห้ามเขียนสิ่งต่อไปนี้ลงใน `retro_envelope.md`:

```text
- ข้อความเชิง prose ประเภท "What worked" / "What failed"
- หัวข้อ "Lessons learned" / "Root cause" / "Future recommendation"
- การตัดสินเชิงคุณค่า
- การเสนอ doctrine
- การเปรียบเทียบคุณภาพกับ session ก่อนหน้า
- การทำนาย session ในอนาคต
- ข้อเสนอแนะการเปลี่ยน policy
- Embeddings / vectors / similarity scores
- การ auto-pin / auto-promote
```

รายการนั้นคือ operational expansion ของ Article IX ถ้าเห็นวลีพวกนี้
อยู่ใน `retro_envelope.md` แสดงว่า closure path drift ไปแล้วและ spec
ถูกละเมิด

## Cross-References

- Spec canonical: [`docs/specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md`](../specs/TRINITY_RETRO_RRR_SPLIT_SPEC_V1.md)
- Python contract: `.ai/cli/core/retro_rrr_contract.py`
- RRR Delegation Contract v1.0: [`docs/constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md`](../constitution/contracts/TRINITY_RRR_DELEGATION_CONTRACT_V1.md)
- Article IX (Memory Discipline) + Article IV (Separation): [`docs/constitution/TRINITY_CONSTITUTION_V1.md`](../constitution/TRINITY_CONSTITUTION_V1.md)
- ภาพรวม ritual loop: [`03_RITUAL_LOOP.md`](03_RITUAL_LOOP.md)

```text
rrr writes facts.
retro writes meaning.
human pins authority.
audit records all three.
```

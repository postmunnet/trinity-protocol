# Trinity คืออะไร

Trinity คือ governance kernel สำหรับงานที่ใช้ AI ช่วยทำ ไม่ใช่ agent
framework ตัวใหม่ และไม่ใช่ external brain วิเศษ

```text
AI agent = worker
Trinity = control plane / supervisor
Artifact = evidence
Verifier = judge
Audit = black box recorder
Memory = artifact recall
Human = final authority
```

## Trinity แก้ปัญหาอะไร

AI มักพูดว่า:

```text
แก้แล้ว
น่าจะผ่าน
ดูโอเคแล้ว
```

Trinity บังคับให้เปลี่ยนเป็น:

```text
มี plan artifact
มี diff
มี test output
มี verifier verdict
มี audit event
```

## Pyramid of Judgment

```text
verifier rules -> policy gates -> LLM judge -> human
```

AI อยู่ชั้น advisory/execution ไม่ใช่ final authority

## สิ่งที่ Trinity ไม่ claim

- ไม่ guarantee correctness
- ไม่แทน human deploy approval
- ไม่ทำ production full auto โดยไม่มี gate
- ไม่ให้ memory ตัดสิน truth

Trinity เพิ่ม auditability, verification, and operational discipline.

# Artifact Truth

หลักของ Trinity:

```text
No artifact = no trust
No verification = no completion
```

AI claim แบบนี้ไม่พอ:

```text
ผมแก้แล้ว
น่าจะผ่าน
ไม่มีปัญหา
```

ต้องมี evidence:

```text
pytest output
diff/stat
verifier report
release evidence
audit event
export manifest
```

## Artifact ตัวอย่าง

- `THINK/plan_envelope.json`
- `THINK/02_SCOPE.md`
- `THINK/03_ACCEPTANCE.md`
- `CAPTURE/...`
- `docs/releases/TRINITY_V0_1_0_RELEASE_EVIDENCE.md`
- `EXPORT_MANIFEST.md` ใน generated export

## Memory ไม่ใช่ Truth

`memory-cli` ใช้ค้นและ recall artifact ที่ index แล้ว

```text
rrr -> memory-cli index <retro-path>
```

ไม่ใช่:

```text
rrr -> memory-cli learn
```

Memory retrieves; it does not judge.

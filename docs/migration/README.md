---
title: "trinity_v2 Migration Plan — Index"
status: locked
last-updated: 2026-05-17
purpose: "Single source of truth for the trinity_v2 setup work. Read these documents before executing any commit."
---

# trinity_v2 Migration Plan

> **กฎเหล็ก:** ก่อน execute commit ใดๆ ต้องอ่านเอกสารในโฟลเดอร์นี้ทั้งหมด ห้ามเดา

## 📑 เอกสาร 5 ไฟล์ — อ่านตามลำดับ

| # | ไฟล์ | เนื้อหา | อ่านเมื่อ |
|---|------|---------|---------|
| 1 | [`01_CONTEXT_AND_DECISIONS.md`](01_CONTEXT_AND_DECISIONS.md) | ทำไมต้องมี trinity_v2 · source projects 4 ที่ · locked decisions พร้อมเหตุผล | ครั้งแรกของทุก session |
| 2 | [`02_EVIDENCE_TRIAGE.md`](02_EVIDENCE_TRIAGE.md) | ผล Commit 0 (evidence gathering) · `ai status` พังตรงไหน · B1-B4 = myth · uncommitted scope | ก่อน Commit 1 |
| 3 | [`03_COMMIT_PLAN.md`](03_COMMIT_PLAN.md) | Commit 0–7 ละเอียด: goals, files, sub-tasks, acceptance criteria, spec refs | ทุกครั้งที่ execute commit |
| 4 | [`04_ENHANCEMENTS.md`](04_ENHANCEMENTS.md) | Star's 2 final enhancements: YAML validation hook · relative-path ssot.yaml | ระหว่างทำ Commit 1 + 2 |
| 5 | [`05_REVIEW_LOG.md`](05_REVIEW_LOG.md) | Decision history: Codex/Gemini/Claude/Star iterations · ทำไม decision X ถึงเป็น Y | เมื่อสงสัย "ทำไมเลือกแบบนี้" |

## 🎯 Status สรุป

- **Commit 0 (Evidence):** ✅ DONE
- **Commit 1 (Make runnable):** ⏳ ready to execute
- **Commit 2 (Phase 0.5 stubs):** ⏳ ready to execute
- **Commit 3–7:** 📋 planned

## 🔗 Cross-references

- Trinity v2 specs: [`../specs/INDEX.md`](../specs/INDEX.md) · [`../specs/00_BLUEPRINT.md`](../specs/00_BLUEPRINT.md)
- Project entry: [`../../README.md`](../../README.md)
- Vendor entry: [`../../CLAUDE.md`](../../CLAUDE.md) · [`../../AGENTS.md`](../../AGENTS.md)

## ⚠️ ห้าม

- ❌ Execute commit โดยไม่อ่าน `03_COMMIT_PLAN.md` ของ commit นั้นก่อน
- ❌ เปลี่ยนแปลง decisions ใน `01_CONTEXT_AND_DECISIONS.md` โดยไม่ update `05_REVIEW_LOG.md`
- ❌ Copy ไฟล์จาก <upstream-project> / TRINITY_LEGACY โดยไม่ตรวจ contamination ตาม `02_EVIDENCE_TRIAGE.md`

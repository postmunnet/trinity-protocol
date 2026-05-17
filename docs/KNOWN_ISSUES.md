# Known Issues

This file records runtime issues that are known but not yet fixed. Keep entries
short, reproducible, and linked to source evidence when possible.

## Open

_(none currently open)_

## Resolved

| ID | Severity | Title | Area | Resolution |
|---|---|---|---|---|
| KI-2026-05-16-001 | high | Global active-session routing can send rituals to the wrong session | session runtime / multi-agent | Session 9 (2026-05-16) — `--session` flag on vvv/nnn/gogogo (mirroring rrr's pre-existing flag); emits `kernel.session_override` audit row on bypass; shared `core.session_resolver.resolve_explicit_session` helper |
| KI-2026-05-16-002 | medium | Next-action footer is not unified across all ritual paths | ritual UX / next-action | Session 17 (2026-05-16) RESOLVED — session.py / close.py / gogogo.py blocked-path now route through `core.next_action.compute + render_one_line`; legacy `ai snapshot` recommendation removed from session.py; LIVE_MONITOR template updated to canonical workflow; test coverage added for READY/THINK/DO/DEPLOYED/RETRO + no-active-session + JSON↔footer agreement |

## KI-2026-05-16-001 — Global Active-Session Routing Drift

Status: RESOLVED 2026-05-16 (Session 9 — see commit on main)

Severity: high

Area: session runtime, ritual routing, multi-agent safety

Observed on: 2026-05-16

### Summary

Trinity ritual commands currently resolve the active session through the shared
global `.ai/state/status.json.current_session`. In a busy or parallel workflow,
that singleton can point at a different session than the one the operator just
created. The result is that `vvv`, `nnn`, or `gogogo` may write artifacts and
audit events into the wrong session capsule.

This is dangerous for multi-agent parallel work because each agent can believe
it owns a distinct session while the kernel routes subsequent rituals through a
shared mutable pointer.

### Evidence From Local Run

During the checklist-index task:

1. `bash .ai/cli/ai sss "เพิ่ม .ai/checklists เป็น index กลางแยก release tool policy session deploy prd-handoff"`
   created session `0002_2026-05-16_10_37_am_feat-เพิ่ม-ai-checklists-เป็น-index-กลางแยก-r`.
2. Immediately after, `bash .ai/cli/ai status` reported no active session and
   `lll` showed that same session had already emitted close events.
3. `bash .ai/cli/ai session new "เพิ่ม .ai/checklists เป็น index กลาง"` created
   session `0002_2026-05-16_10_37_am_feat-เพิ่ม-ai-checklists-เป็น-index-กลาง`.
4. Running `bash .ai/cli/ai vvv ...` then wrote the prompt and marker under
   `.ai/sessions/0003_2026-05-16_10_37_am_feat-p6-session-g-tool-dispatcher/`
   instead of the checklist session.
5. `bash .ai/cli/ai status path` confirmed the active session had become
   `.ai/sessions/0003_2026-05-16_10_37_am_feat-p6-session-g-tool-dispatcher`.

### Impact

- Parallel agents can cross-write session artifacts.
- `vvv`/`nnn`/`gogogo` evidence may attach to the wrong goal.
- Audit remains hash-valid but semantically misleading.
- A human gate may review artifacts from a mixed session.
- Session closure can archive a session before the intended workflow has run.

### Suspected Cause

Ritual commands use a repo-global active-session pointer instead of a
session-scoped execution lease or explicit session path. Session-local state,
graph state, and the global current-session pointer can drift apart.

### Fix Direction

- Add explicit `--session-path` support to mutating rituals or require a
  kernel-issued session lease for each agent.
- Make `sss`/`session new` atomically set and verify the created session as the
  active session before returning.
- Refuse `vvv`/`nnn`/`gogogo` if the active session id does not match the
  caller's declared session id.
- Add a parallel-session regression test with two sessions interleaved.
- Make `lll`/`status` surface global-vs-local session drift as a blocking
  warning, not just a stale-session hint.

### Acceptance For Fix

- [ ] Two sessions can be created and advanced independently without cross-write.
- [ ] `vvv` writes `THINK/01_PROMPT.md` only under the declared session.
- [ ] `nnn` writes `.state/plan.json` only under the declared session.
- [ ] `gogogo` refuses to run when global and declared session ids disagree.
- [ ] Audit events include the correct session id for every ritual.
- [ ] `bash .ai/cli/ai doctor commands` passes.
- [ ] `cd .ai && python3 -m pytest cli/tests -q` passes.

## KI-2026-05-16-002 — Next-Action Footer Not Unified Across Rituals

Status: RESOLVED 2026-05-16 (Session 17 — see commit on main)

Severity: medium

Area: ritual UX, next-action, implementation consistency, multi-agent guidance

Observed on: 2026-05-16

### Summary

The CLI has a central next-action module and most ritual success paths already
print a "what to do next" footer. However, the behavior is not yet unified
across every ritual and terminal path.

This matters because operators and parallel agents should be able to trust the
ritual output after every command, especially after the global active-session
routing issue fixed in KI-2026-05-16-001. If different commands print different
or stale next-step guidance, agents can still follow the wrong workflow even
when session routing is correct.

### Evidence From Local Inspection

- `.ai/cli/core/next_action.py` defines the central next-action computation and
  renderer.
- `.ai/cli/commands/lll.py`, `vvv.py`, `nnn.py`, `gogogo.py`, `ddd.py`, and
  `rrr.py` use the central next-action footer on success paths.
- `.ai/cli/commands/session.py` still hardcodes `Next Step: ai snapshot` after
  session creation instead of using the central next-action module.
- `.ai/cli/commands/close.py` still hardcodes the post-close suggestion instead
  of routing through the same formatter.
- Some blocked/error paths use ad hoc copy such as "Run `ai next`" rather than
  the same session-aware next-action renderer.

### Impact

- `sss` / `session new` can return stale or inconsistent next-step guidance.
- `close` does not share the same terminal-state behavior as `ai next`.
- Error paths may tell the user to run a generic command without the relevant
  session context.
- Parallel agents need explicit, session-scoped next commands; generic next
  output can be ambiguous when more than one session is active or recently
  touched.

### Fix Direction

- Route `sss` / `session new` success output through
  `core.next_action.compute_next` and `render_one_line`.
- Route `close` terminal output through the same next-action formatter, or
  document a single explicit terminal fallback in that module.
- Add a small shared helper for ritual success and common blocked/error
  footers so commands do not hand-roll next-step text.
- Prefer session-scoped next commands in ritual output where the command has an
  explicit session id or path available.
- Add tests proving ritual footers and `ai next --json` agree for the same
  session state.

### Acceptance For Fix

- [ ] `sss` / `session new`, `vvv`, `nnn`, `gogogo`, `ddd`, `rrr`, `lll`, and
      `close` all display next-action output from one shared module or a
      documented terminal fallback.
- [ ] `session new` no longer recommends `ai snapshot` unless `ai next`
      computes that command for the current state.
- [ ] `close` prints terminal/new-session guidance through the same formatter.
- [ ] At least one blocked/error path is covered by the shared next-action
      footer helper.
- [ ] `ai next --json` and each ritual footer agree for the same session and
      graph state.
- [ ] Tests cover READY, THINK, DO, VERIFIED, DEPLOYED, RETRO, DONE, and no
      active-session states.
- [ ] `bash .ai/cli/ai doctor commands` passes.
- [ ] `cd .ai && python3 -m pytest cli/tests -q` passes.

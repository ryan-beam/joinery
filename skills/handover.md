---
name: handover
description: |
  Generate HANDOVER.md from current session state. Captures what got done, what's next, open side quests, and notes for the next session. Triggers when user says "I'm wrapping up", "end of session", "pause here", "taking a break", "let's pick this up next time", or auto-fires via workshop session end.
---

# /handover — session-end handoff

## When to use

Fires at end of session. Auto-invoked by `workshop session end`. Read at the start of the next session by `workshop session start`.

Triggers:
- "I'm wrapping up" / "end of session" / "pause here"
- "taking a break" / "let's pick this up next time"
- Auto-fires at `workshop session end`

## Procedure

1. **Read the session's commit history** since the last `workshop session start` (or last 24 hours if no session-start marker).

2. **Read the current `plan.md` status.** Which sections are populated? Is the plan still in drafting, or has it advanced?

3. **Read `learning/side-quests.md`** to identify open SQs.

4. **Compose HANDOVER.md** with four sections:

   **What got done last session:** plain-English bullet list of meaningful changes. Reference commits where useful.

   **What's next:** what to pick up first when the user comes back. If `plan.md` has unchecked success criteria, the natural next step is to keep cutting toward them. If the plan is still drafting, identify what section needs work.

   **Open side quests:** auto-pulled from `learning/side-quests.md`, filtered to "open" status. List the 3-5 hottest (oldest unresolved + most recently captured).

   **Notes for next-self:** anything that won't be obvious from the diff. Stale assumptions, half-finished thoughts, decisions deferred, conversations to continue.

5. **Update HANDOVER.md frontmatter** with `last_session_end` (current ISO timestamp), `branch` (current git branch), `plan_status` (read from plan.md frontmatter).

6. **Overwrite, don't append.** HANDOVER is the CURRENT state, not an archive. The previous handover gets archived to `docs/handovers/<date>.md` if `[features] archive_handovers = true` (default off; production tier turns on).

## Output format

A populated `HANDOVER.md` at project root. Frontmatter + four sections.

## Examples

```markdown
# HANDOVER

**Last session ended:** 2026-05-12 22:30 UTC
**Active branch:** feat/auth-flow
**Current plan status:** active

## What got done last session

- Added signup form validation (commit a1b2c3): email format, password complexity, uniqueness check
- Wrote failing tests for SC-1 through SC-4 (commit b2c3d4)
- Started implementing the SignupForm component (commit c3d4e5) — component shell + email field done

## What's next

- Continue SignupForm implementation: password field, submit handler
- Run /mark on Section 3.5+ if any success criteria emerged during cutting
- The /api/check-email endpoint isn't real yet — stub for now or wire up backend?

## Open side quests

- SQ-031 — Tailwind v4 layer cake (oldest open, 6 days)
- SQ-042 — useDeferredValue: when does it actually defer? (captured this session)
- SQ-043 — debounce vs throttle for input checks (captured this session)

## Notes for next-self

- The validation strategy assumes server-side validation also exists. Worth confirming with the backend team before merging.
- Considered react-hook-form but went hand-rolled. If we add 3+ more forms, revisit.
- The "uniqueness check stub vs real" question above is a real fork in the road — pick before next session.
```

## Notes

- Token cost ~500 tokens. Effectively free.
- The handover is the next session's preflight. Make it useful, not ceremonial.
- Don't fabricate. If you don't know what's next, say "open question — decide first thing next session."

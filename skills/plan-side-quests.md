---
name: plan-side-quests
description: |
  At the end of a planning conversation, scan the plan and conversation for concepts the user doesn't fully grok yet. Populate Section 5 (Side quests) of plan.md and auto-log entries to learning/side-quests.md. Composed by /plan, or invoked manually with "log side quests from this", "what concepts did I gloss over", "extract learning gaps".
---

# /plan-side-quests — extract learning gaps from planning

## When to use

Composed by `/plan` near the end of the conversation, after sections are populated. Also manually invokable to retroactively extract side quests from a planning thread.

## Procedure

1. **Re-read the planning conversation.** Look for moments where a concept, library, or pattern came up and the user:
   - Asked "what is X" / "how does X work"
   - Said "I'm not sure about X" / "I don't fully understand X"
   - Hand-waved through an explanation
   - Accepted the agent's framing without engaging

2. **Surface candidate side quests.** For each, ask the user: "Is this familiar to you, or worth logging as a side quest?"

   Example: "We're using `useDeferredValue` for the form input filtering. Are you familiar with how it differs from `useTransition`, or should I log a side quest?"

3. **For each confirmed gap, write an entry** to `learning/side-quests.md`:
   ```markdown
   ## SQ-NNN: <concept>
   - **Captured:** {{today_iso_with_time}}
   - **Where:** plan.md §<section>, <one-line context>
   - **What I don't get:** <user's own words about the gap>
   - **Status:** open
   - **Resources collected:**
     - [ ] <relevant doc, blog post, or "research needed">
   - **What I now understand:** (filled at closure via /sq close)
   ```

4. **Populate Section 5 of plan.md** with checkbox entries pointing at the SQ-NNN ids:
   ```markdown
   ## 5. Side quests

   - [ ] [SQ-042](learning/side-quests.md#sq-042) — useDeferredValue: when does it actually defer?
   - [ ] [SQ-043](learning/side-quests.md#sq-043) — Tailwind v4 layer cake
   ```

5. **Don't auto-close** anything. Side quests are open until the user explicitly closes via `/sq close SQ-NNN` after a learning session.

## Output format

- Updated `learning/side-quests.md` with new SQ-NNN entries appended
- Updated Section 5 of `plan.md` with links to those entries

## Notes

- Don't fabricate side quests. Only log what the user confirmed as a real gap.
- Don't filter for "easy" topics. The whole point of the learning module is making the gaps visible.
- SQ-NNN ids are auto-incremented — read the highest existing SQ-NNN in `learning/side-quests.md` and increment.

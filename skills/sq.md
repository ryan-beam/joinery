---
name: sq
description: |
  Capture a side quest entry — a concept, library, or pattern the user doesn't fully grok yet. Auto-invoked by /plan-side-quests during planning and during cutting when the agent flags uncertainty; also manually invokable. Triggers when user says "I don't get X", "what is X", "why does X work that way", "I'm fuzzy on X", "explain X to me later", "log a side quest for X".
---

# /sq — manual side quest entry

## When to use

Captures a concept the user wants to learn but isn't pausing for right now. Stays in `learning/side-quests.md` until closed.

Triggers:
- "I don't get X" / "what is X" / "why does X work that way"
- "I'm fuzzy on X" / "explain X to me later"
- "log a side quest for X" / "/sq X"
- Auto-invoked by `/plan-side-quests` and during cutting when uncertainty surfaces

## Procedure

1. **Read existing entries** in `learning/side-quests.md` to find the next SQ number.

2. **Compose the entry:**

   ```markdown
   ## SQ-NNN: <concept>
   - **Captured:** <YYYY-MM-DD HH:MM>
   - **Where:** <plan section, file, conversation context — what triggered it>
   - **What I don't get:** <one-line in user's words>
   - **Status:** open
   - **Resources collected:**
     - [ ] <link or note — "research needed" if no resource yet>
   - **What I now understand:** (filled at closure via /sq close)
   ```

3. **Append to `learning/side-quests.md`.** Don't rewrite the file; just append.

4. **Don't auto-close.** Side quests stay open until the user explicitly closes via `/sq close SQ-NNN` after a learning session. Even if the user seems to understand the concept later, the explicit close ritual is what triggers the skills-log entry.

## Closure path: `/sq close SQ-NNN`

When the user runs `/sq close SQ-NNN`:

1. Read the SQ entry. Confirm with the user that they actually understand it now.
2. Set status from `open` to `done`.
3. Fill in **What I now understand** with the user's plain-language explanation (their words, not the agent's).
4. Append a new entry to `learning/skills-log.md`:
   ```markdown
   ## YYYY-MM-DD — <concept>
   - **Source:** SQ-NNN, <docs / blog / conversation>
   - **What I now understand:** <user's explanation>
   - **Used since:** <commit hash or "not yet">
   ```
5. Commit:
   ```
   learning: close SQ-NNN — <concept>
   ```

## Output format

For new SQ: appended entry in `learning/side-quests.md` with auto-incremented number.
For closure: status flipped + skills-log entry appended.

## Notes

- Token cost ~200 for capture, ~500 for closure. Effectively free.
- SQ entries stay in the file forever. Don't delete — they're the durable record of learning.
- The "What I now understand" field is the user's plain-language synthesis. Don't outsource this to the agent — that defeats the comprehension purpose.

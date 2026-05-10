---
name: audit
description: |
  Scaffold the comprehension audit ritual. Selects a recent commit, prompts the user for a cold explanation, scores honestly, files SQ entries from gaps. The skill scaffolds — the user writes the explanation. MANUAL ONLY (or /digest prompts when overdue). Triggers when user says "let's do an audit", "comprehension check", "/audit", "time for the weekly audit".
---

# /audit — comprehension audit scaffold

## When to use

**Manual only**, with cadence enforcement via `/digest` reminders. The framework can't write the audit for you (that defeats the comprehension purpose), but it can make the absence loud.

Triggers:
- "/audit" (explicit invocation)
- "let's do an audit" / "comprehension check"
- "time for the weekly audit"

Cadence: `/digest` flags when an audit is overdue per `[learning] audit_trigger` config (default: every 20 commits OR 14 days).

## Procedure

1. **Read recent commits** on the current branch (or main if not on a feature branch). Pick a commit that:
   - Touched non-trivial code (not a typo fix or version bump)
   - Was authored recently (within the audit trigger window)
   - The user hasn't audited yet (cross-reference `learning/comprehension-audits.md`)

   If multiple candidates, ask the user to pick one.

2. **Surface the commit** by hash and one-line summary, but **do not show the diff yet.** The point of cold explanation is testing what the user remembers/understands without rereading.

3. **Prompt the user:**

   > "Without looking at the code, explain this flow in plain language. What does it do, why was it built that way, what tradeoffs were made? Take your time."

4. **Capture their cold explanation** verbatim. Don't paraphrase.

5. **After they finish, show them the diff** alongside their explanation. Ask:

   > "Now compare your explanation to the code. What did you wave hands at? What surprised you? What couldn't you explain cleanly?"

6. **Identify gaps.** For each gap, log a side quest via `/sq <concept>`.

7. **Score 1-5:**
   - 5 = solid understanding everywhere
   - 4 = solid on the flow, hand-wavy on one piece
   - 3 = solid on the goal, fuzzy on the mechanics
   - 2 = could describe what but not why
   - 1 = couldn't explain at all

8. **Write the audit entry** to `learning/comprehension-audits.md` (newest at top):

   ```markdown
   ## Week W## — YYYY-MM-DD

   **Audited:** <description>, commit <hash>

   **Cold explanation:**
   > <user's explanation, verbatim>

   **Gaps found:**
   - <thing they waved hands at> → SQ-NNN
   - <thing they couldn't explain> → SQ-NNN

   **Score:** N/5
   ```

9. **Discipline note:** Score under 3 = comprehension debt. Surface this to the user with the message "Pay this debt before the next big build. Re-audit this area within a week after closing the gap SQs."

## Output format

- A new audit entry prepended to `learning/comprehension-audits.md`
- Zero or more new SQs appended to `learning/side-quests.md`

## Notes

- The audit is human-written. The agent scaffolds, prompts, and records — never writes the cold explanation itself.
- Score 5/5 on a complex audit is suspicious. Honest scoring is the only thing that makes this real.
- Cadence: trigger-based, not calendar-locked. Active weeks audit on volume; slow weeks get caught by the 14-day fallback.

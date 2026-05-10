---
name: workshop-session-end
description: |
  Compose explain-back, handover, side-quest reconciliation, primary/secondary classification, token report. The session-close ritual. Invoked by the `workshop session end` CLI command. Triggers when user says "ending the session", "wrapping up", "session end", "done for now", "close out this session".
---

# /workshop-session-end — session-close ritual

## When to use

Fires at end of a working session. Invoked automatically by `workshop session end` CLI subcommand. Manually invokable via the trigger phrases.

This is Phase 5 (Finishing) for the session as a unit. Composes multiple sub-skills.

## Procedure

1. **Run `/explain-back`** on the session's commits. Outputs the comprehension-gate transcript.

2. **Show the explain-back to the user.** Pause for the comprehension gate:
   > "Read the explain-back. Anything surprising? Anything you'd phrase differently? Anything we should dig into before closing?"

3. **Side-quest reconciliation.** For each SQ that was opened during this session:
   - "Is this still open, or did the session close it?"
   - If still open: leave as-is
   - If closed: walk through `/sq close SQ-NNN`

4. **Run `/handover`** to overwrite `HANDOVER.md`. Output the new HANDOVER for user to verify.

5. **Primary/secondary classification:** prompt the user with two questions:
   - "Was this session primarily about learning a new thing, or shipping known stuff?"
   - "One-line note?"

   Append a JSONL line to `learning/ratio-log.jsonl`:
   ```jsonl
   {"date":"<YYYY-MM-DD>","type":"primary|secondary","project":"<name>","note":"<one-line>"}
   ```

6. **Token report:** read `.workshop/usage.jsonl` filtered to this session, aggregate by phase:

   ```
   Session ended. Token report:
     Drafting:   3,240 tokens
     Cutting:    47,820 tokens
     Finishing:  4,180 tokens
     Total:      55,240 tokens
     vs avg of last 5 sessions: -12%
   ```

7. **If anything changed in `learning/` during this session** (new SQs, closed SQs, ratio entry), commit it as one final session-end commit:

   ```
   session: <one-line summary of what got done>

   <optional Lore Protocol body if production tier and changes warrant>
   ```

8. **Print the session-end summary:**

   ```
   Session closed. <Brief recap from explain-back: what got done>.

   Side quests: <X> opened, <Y> closed this session.
   Ratio entry: primary | secondary — "<note>"
   Tokens: <total>, trend <+/-N>% vs avg.

   HANDOVER updated. workshop session start picks up here.
   ```

## Output format

- Updated `HANDOVER.md`
- Possibly closed SQs in `learning/side-quests.md`, with corresponding `learning/skills-log.md` entries
- New JSONL line in `learning/ratio-log.jsonl`
- One session-end commit if learning artifacts changed
- Terminal summary

## Notes

- Token cost ~3-5K for the full ceremony (mostly explain-back).
- The comprehension gate (step 2) is the load-bearing step. Don't skip it. If the user reads the explain-back and immediately confirms "yep, that's what we did," that's fine — but they have to actually read it.
- If there's nothing to write to HANDOVER (a quick session that didn't really land anything), say so. Don't fabricate.
- Token report uses `.workshop/usage.jsonl` which is populated by the workshop CLI itself (Phase 4). Until Phase 4 ships, the token report is approximate.

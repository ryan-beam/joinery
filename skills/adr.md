---
name: adr
description: |
  Create a new Architecture Decision Record from a non-trivial decision. Records what was decided, what alternatives were considered, why the chosen one won, and what the consequences are. Triggers when user says "we just decided X over Y", "log this decision", "draft an ADR for this", "this needs to be recorded", "what we just chose is significant".
---

# /adr — create a new Architecture Decision Record

## When to use

Fires when a non-trivial architectural decision is made during cutting (or in a planning conversation that didn't auto-extract via `/plan-decisions`).

Triggers:
- "we just decided X over Y"
- "log this decision"
- "draft an ADR for this"
- "this is worth recording"
- "the decision we just made is significant"

## Procedure

1. **Read existing ADRs** in `docs/decisions/` to find the next number. ADRs are numbered sequentially: 0001, 0002, etc.

2. **Identify the decision.** Ask if needed:
   - "What was the decision?" (one-line summary)
   - "What alternatives were considered?"
   - "Why did the chosen one win?"
   - "What are the consequences going forward?"

3. **Write the ADR file** at `docs/decisions/NNNN-<short-title>.md`:

   ```markdown
   # ADR-NNNN: <decision title>

   **Status:** Accepted
   **Date:** <YYYY-MM-DD>
   **Decider:** <author or team>

   ## Context
   <Why this decision came up. What forced the choice. One paragraph.>

   ## Decision
   <What was decided. Plainly stated. One paragraph.>

   ## Considered alternatives
   <For each alternative, one sentence on what it was and one sentence on why it lost.>

   ## Consequences
   <What this decision means going forward. New constraints, freed-up options, things to watch.>

   ## References
   - <Links: plan.md sections, related ADRs, external docs>
   ```

4. **Title slug** is short, lowercase, kebab-case. e.g., `0042-postgres-over-mysql.md`. The title in the file's first heading uses the human-readable form: "ADR-0042: Postgres over MySQL for the events store".

5. **Link from `plan.md` Decisions log** if the decision came up during planning:
   ```markdown
   - [ADR-0042](docs/decisions/0042-postgres-over-mysql.md) — Chose Postgres over MySQL for the events store
   ```

6. **Commit the ADR** with a message that names what was decided:
   ```
   adr: 0042 — postgres over mysql for the events store
   ```

## Output format

- A new ADR file at `docs/decisions/NNNN-<slug>.md`
- Optional update to `plan.md` Decisions log
- A commit landing the ADR

## Notes

- Status options: Proposed, Accepted, Rejected, Superseded by ADR-NNNN, Deprecated
- "Why the alternatives lost" is the most valuable part. Future-you will read this when revisiting.
- ADRs are append-only history. To change a decision, write a new ADR that supersedes the old one. Never edit accepted ADRs to reverse them.

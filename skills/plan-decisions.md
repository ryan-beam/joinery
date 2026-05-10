---
name: plan-decisions
description: |
  At the end of a planning conversation, surface non-trivial decisions made during planning and seed the Decisions log section of plan.md. Drafts ADR stubs for decisions that warrant standalone treatment. Composed by /plan near the end of the conversation, or invoked manually with "what decisions did we make", "draft ADRs from this conversation", "seed the decisions log".
---

# /plan-decisions — surface decisions made during planning

## When to use

Composed by `/plan` near the end of the planning conversation, after all sections are populated. Also manually invokable to retroactively extract decisions from a long planning thread.

## Procedure

1. **Re-read the planning conversation.** Look for moments where alternatives were weighed and one was chosen. Examples:
   - "We considered X, but went with Y because Z"
   - "Should we use database A or B? → B because..."
   - "We're choosing to defer X to v2 because..."

2. **Filter for non-triviality.** Decisions worth ADRs:
   - Architectural choices that affect multiple components
   - Technology choices (database, framework, language for a subsystem)
   - Tradeoffs that future-you would want to understand
   - Decisions to defer or NOT do something

   Skip:
   - Implementation details (which loop construct, which library helper)
   - Style choices (covered by CLAUDE.md)
   - Decisions that don't have alternatives weighed

3. **For each decision, draft an ADR stub** at `docs/decisions/NNNN-<short-title>.md`:
   ```markdown
   # ADR-NNNN: <decision title>

   **Status:** Proposed (will be Accepted when this plan is approved)
   **Date:** {{today}}
   **Decider:** <author>

   ## Context
   <Why this decision came up>

   ## Decision
   <What was decided>

   ## Considered alternatives
   <What else was weighed and why it lost>

   ## Consequences
   <What this means going forward>

   ## References
   - plan.md §X
   ```

4. **Seed the Decisions log section of plan.md** with a one-liner per ADR:
   ```markdown
   - [ADR-NNNN](docs/decisions/NNNN-<slug>.md) — <one-line summary>
   ```

5. **Surface decisions that DIDN'T meet the bar** in a single bullet at the end of plan.md as "Minor decisions (not ADR-worthy):". Keeps the surfacing complete without forcing ceremony.

## Output format

- New ADR files at `docs/decisions/`
- Updated `plan.md` Decisions log section with links to each ADR
- Optional bullet list of minor decisions in plan.md

## Notes

- 0-3 ADRs per planning conversation is typical. More than 5 = bar too low; cut to the load-bearing ones.
- ADRs can stay in "Proposed" until the plan is approved. Status flips to "Accepted" when the plan does.

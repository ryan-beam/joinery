---
name: docs-architecture
description: |
  Refresh docs/architecture.md from the current code structure and relevant ADRs. Produces a 1-page system overview that matches what the code actually looks like. Triggers when user says "update architecture doc", "the architecture changed", "redraw the system overview", "refresh docs/architecture.md".
---

# /docs-architecture — refresh the architecture doc

## When to use

Manually invokable when the system's structure has changed meaningfully. Auto-suggested by `/docs` orchestrator when this file is detected as stale.

Triggers:
- "update architecture doc" / "redraw the system overview"
- "the architecture changed"
- "refresh docs/architecture.md"
- Composed by `/docs` when stale

## Procedure

1. **Read the current code structure.** Top-level directories, primary modules, key entry points. Don't enumerate every file — capture the meaningful subsystems.

2. **Read accepted ADRs** in `docs/decisions/`. The ADRs document the architectural decisions; the doc should reflect them.

3. **Read existing `docs/architecture.md`.** Identify what's still accurate vs what's drifted. Don't rewrite from scratch if most is fine — surgical updates beat full rewrites.

4. **Update sections of the doc:**

   - **What it is** — one paragraph, project purpose
   - **Top-level structure** — list of meaningful subsystems with one-line descriptions
   - **Key flows** — pointer to `plan.md` Section 7 if exists, or summarize the 1-2 most important flows
   - **Technology choices** — what runtime, framework, database; reference ADRs that decided each
   - **Configuration** — pointer to relevant config files
   - **Where to learn more** — links to spec, ADRs, plan

5. **One page.** This doc is the gateway, not the full design. Long-form design lives in spec.md (if applicable) or ADRs. If `docs/architecture.md` is growing past one screen, that's a smell.

6. **Commit:**

   ```
   docs: refresh architecture.md after auth restructure
   ```

## Output format

Updated `docs/architecture.md` — one page, navigable, current.

## Notes

- One page maximum. If you need more, it's belongs in ADRs or a longer spec doc.
- Reference ADRs liberally — they document the WHY. The architecture doc covers the WHAT.
- Don't fabricate. If the codebase is messier than the diagram suggests, surface that — the doc shouldn't be aspirational.

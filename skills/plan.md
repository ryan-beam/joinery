---
name: plan
description: |
  Drive an unbounded planning conversation to produce a project plan.md. Composes sub-skills as the conversation develops. Leverages Claude Code plan mode when available; works without it otherwise. No turn cap — runs until the plan converges. Triggers when user says "let's plan X", "plan this", "design X", "draft a plan for Y", "we need to think through how to build Z", or any request to structure thinking before coding.
---

# /plan — the planning orchestrator

## When to use

Fires at the start of meaningful new work: a feature, a refactor, a project, a significant change. Output is a populated `plan.md` at project root per `docs/spec.md` §6 structure.

## Procedure

1. **Detect environment.** If running in Claude Code, recommend the user enter plan mode (Shift+Tab or their keybinding). Plan mode's question-driven, no-turn-cap, read-only behavior is exactly what this skill needs. If outside Claude Code, drive the same conversation manually.

2. **Gather context first.** Before drafting sections, ask:
   - "What are you trying to build?"
   - "Is there prior research or related work? Paste it in for the Context section."
   - Read `docs/spec.md`, recent commits, relevant files. Surface what you know.

3. **Iterate section by section** per `docs/spec.md` §6 structure: Context (optional) → Problem → Approach → Success criteria → Forbidden actions → Side quests → Data model (conditional) → Critical flows (conditional).

4. **Lengths are flexible.** A typo-fix plan might be one sentence per section; a complex production plan might have 15 paragraphs in Problem. Guide structure, not length.

5. **Ask clarifying questions liberally.** Re-ask when answers are vague. Surface your own uncertainty.

6. **Pause for context dumps.** Prior research, transcripts, conversation summaries — pause for them. Goes into Section 0.

7. **Iterate sections out of order if needed.** Approach might require Data model first. Don't force linear order.

8. **Refine until convergence.** Routine work might converge in 3-5 rounds; complex work in 20+. The plan is done when it's done.

9. **Compose sub-skills as the plan develops:**
   - Architecture surface → `/plan-system` (Mermaid + Files in scope)
   - Persistent state → `/plan-data` (ER diagram)
   - Non-trivial flows → `/plan-flows` (sequence diagrams)
   - End of conversation → `/plan-decisions` (seed Decisions log) and `/plan-side-quests` (populate Section 5)

10. **Write `plan.md`.** Frontmatter: status, tier (read from `framework.config.toml`), last-updated date, related links. All required sections populated.

11. **Post-process:** Extract Section 5 entries to `learning/side-quests.md` as SQ-NNN. Set status to "active".

## Output format

A complete `plan.md` at project root with frontmatter, all required sections, conditional sections as appropriate, Decisions log with seed entries.

## Notes

- Token-uncapped. Conversation runs as long as it needs to.
- Auto-extracts side quests to `learning/side-quests.md`.
- Hands off to `/mark` (Phase 3) when the user signals "let's start coding".

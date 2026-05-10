# AGENTS.md

> Mirror of `CLAUDE.md` for Cursor / Codex / other agent compatibility. During Phase 3, a pre-commit hook will keep these in sync automatically. Until then, manual mirror.

---

# CLAUDE.md

> Five starter rules for working on Joinery. Each is meant to be refined or replaced by `/rule` commits as real failures surface during the build. Don't add rules from theory.

1. **Think before coding.** State the problem in one paragraph before any edit. If the problem isn't clear in plain English, the code can't be either.

2. **Simplicity first.** Fewer dependencies, fewer abstractions, fewer files. Add complexity only when a concrete need appears, not because it might be needed later.

3. **Surgical changes.** Touch only what the plan says is in scope. If you discover a related fix is needed, surface it as a side quest — don't silently fold it in.

4. **Goal-driven.** Every change ties to a success criterion in `plan.md`. If a change doesn't, ask why it's being made.

5. **Files outside `plan.md` §2 ("Files in scope") are off-limits.** If your edit touches a file not listed there, stop. Surface the deviation. Either update the plan and continue, or split the work into a new plan.

---

## Project context

Joinery is a personal coding framework being built across 6 phases. See `plan.md` for the build plan, `docs/spec.md` for the full design spec, `docs/architecture.md` for a 1-page summary.

This project is **production tier** — Joinery itself uses production-tier discipline (full plan-gate, tdd-gate, ADRs required, structured commits required, branch+PR required on all changes). The framework eats its own dogfood.

## Working on this codebase

- Code style follows the workshop-level defaults (no emojis in code, comments earn their place, descriptive names, ISO dates, UTC times, forward slashes in paths even on Windows). See `docs/spec.md` §11 "Workshop-level defaults" for the full list.
- All commits to production-tier projects use the Lore Protocol commit format above the threshold (see `docs/spec.md` §13).
- Changes to `CLAUDE.md` happen through the `/rule` workflow (one rule per commit, linked to the failure that prompted it). See `docs/spec.md` §11.

## Build phase status

Currently: **Phase 0 (Foundation)** — repo skeleton, root docs, ADRs.

Subsequent phases:
1. Project Templates (markdown files in `templates/`)
2. Skills (markdown files in `skills/`)
3. Hooks (bash scripts in `hooks/`)
4. Workshop CLI (Python in `src/joinery/`)
5. First Dogfood (real production work using Joinery)

# CLAUDE.md

> Five starter rules for working on Joinery. Each is meant to be refined or replaced by `/rule` commits as real failures surface. Don't add rules from theory.

1. **Think before coding.** State the problem in one paragraph before any edit. If the problem isn't clear in plain English, the code can't be either.

2. **Simplicity first.** Fewer dependencies, fewer abstractions, fewer files. Add complexity only when a concrete need appears, not because it might be needed later.

3. **Surgical changes.** Touch only what the plan says is in scope. If you discover a related fix is needed, surface it as a side quest — don't silently fold it in.

4. **Goal-driven.** Every change ties to a success criterion in `plan.md`. If a change doesn't, ask why it's being made.

5. **Files outside `plan.md` §2 ("Files in scope") are off-limits.** If your edit touches a file not listed there, stop. Surface the deviation. Either update the plan and continue, or split the work into a new plan.

---

## Project context

Joinery is a personal coding framework for the AI-agent era — installable via `pip install -e .` and used in projects via `workshop init`. See `docs/architecture.md` for the system overview, `docs/spec.md` for the full design specification.

This project runs on **production tier** — Joinery eats its own dogfood. Production tier discipline applies: branch + PR for all changes (no direct main pushes), Lore Protocol-flavored commit messages on commits over 10 lines changed, mypy --strict + ruff check + ruff format clean, all tests passing.

## Working on this codebase

- Code style follows the workshop-level defaults: no emojis in code or configs, comments earn their place, descriptive names, ISO 8601 dates, UTC times, forward slashes in paths even on Windows. See `docs/spec.md` §11 "Workshop-level defaults" for the full list.
- All production-tier commits over 10 lines use the Lore Protocol commit format (see `docs/spec.md` §13).
- Changes to this `CLAUDE.md` happen through the `/rule` workflow (one rule per commit, linked to the failure that prompted it). See `docs/spec.md` §11.

## v1 status

v0.1.0 shipped on 2026-05-10. The framework is functionally complete; next step is real-world dogfooding (Phase 5) to surface friction and iterate to v1.1. See `plan.md` and `CHANGELOG.md`.

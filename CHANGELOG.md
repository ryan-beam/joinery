# Changelog

All notable changes to Joinery are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — `workshop adopt`

Mid-project adoption command for installing the framework into an existing codebase. Where `init` requires an empty target and scaffolds a fresh project, `adopt` overlays Joinery onto whatever is already there:

- `workshop adopt [--tier T] [--lang L] [--path P] [--force] [--no-hooks]` — runs in the current directory by default
- **Non-destructive by default.** Existing files (`README.md`, prior `CLAUDE.md`, etc.) are preserved and reported, not overwritten. `--force` opts into overwriting framework files.
- **Refuses re-adoption.** If `.workshop/tier.lock` already exists, the command exits with a clear error message unless `--force` is passed.
- **Does not auto-commit.** Files are written to the working tree; the user reviews the diff and stages them through their normal git workflow.
- **Handles non-git targets.** Adopts framework files but skips hook installation, with a printed note explaining how to install hooks after `git init`.
- Project name is derived from the target directory's name; language auto-detected from existing files (Python / TypeScript / polyglot) with a fallback to `polyglot` when nothing matches.

### Changed — `init.py` refactor (internal)

`scaffold()` now composes six module-level helpers (`write_project_files`, `write_learning_module`, `write_tier_adr`, `write_workshop_state`, `install_skills`, `install_hooks_into`) instead of inlining the file-laying logic. The same helpers back `adopt()` with `skip_existing=True`. Public API unchanged — `scaffold()` signature and return type are identical. `copy_template` and `copy_tree` in `templates.py` gain an optional `skip_existing=False` keyword for the same purpose.

### Tests

18 new tests in `tests/test_adopt.py`. Full suite now 60 passing (was 42).

## [0.1.0] — 2026-05-10

First pre-alpha release. The complete v1 framework: templates, skills, hooks, and the workshop CLI. Built from a 2000-line design specification and dogfooded on itself (production-tier discipline applied from the first commit).

### Added — workshop CLI

Python click-based command-line tool, installable via `pip install -e .` (or `pipx install joinery-cli` once published).

- `workshop init <name>` — scaffold a new project (interactive or flag-driven). Reads tier-variant templates, renders Jinja2 placeholders, installs hooks, copies skills, initializes git, makes initial commit.
- `workshop session start` — reads HANDOVER, runs preflight (git status, plan freshness on production), prints session-start summary.
- `workshop session end` — frames the session-end ritual; agent-driven steps via `workshop-session-end` skill.
- `workshop promote <project> --to <tier>` — additive scaffold upgrade (sketch → standard → production). Refuses demotion.
- `workshop doctor` — verifies workshop + project health (config, hooks, sync state, plan freshness).

Modules in `src/joinery/`: cli, init, session, promote, doctor, lang, config, templates, git, paths. Dependencies: click, jinja2. Python 3.11+.

42 pytest tests passing. mypy --strict clean. ruff check + format clean.

### Added — 23 skills

Composable markdown skill files in `skills/`. Auto-invoke from natural language for most; manual-only for `rule`, `audit`, `security-review` where intentionality matters; hook-fired or composed for the rest.

- Planning (6): `plan` (orchestrator, leverages Claude Code plan mode), `plan-system`, `plan-data`, `plan-flows`, `plan-decisions`, `plan-side-quests`
- Workflow (7): `mark`, `explain-back`, `handover`, `review`, `security-review`, `adr`, `pr`
- Discipline (4): `rule`, `sq`, `audit`, `digest`
- Documentation (4): `docs`, `docs-changelog`, `docs-getting-started`, `docs-architecture`
- Session (2): `workshop-session-start`, `workshop-session-end`

Audit-first applied — `/review` and `/security-review` adopt Claude Code's built-in skills as the priority path (engine order: roborev > Claude Code built-in > Claude subprocess fallback).

### Added — 4 git hooks

Bash scripts in `hooks/` that `workshop init` installs into `.git/hooks/` of scaffolded projects.

- `pre-commit` — lint + type-check on staged files + AGENTS.md mirror from CLAUDE.md
- `pre-push` — refuses direct main pushes on production; reads `reviews/` for critical findings
- `commit-msg` — Lore Protocol structure on production-tier commits over threshold; bot author bypass
- `post-merge` — preflight refresh + quick lint surface

Each hook under 50 lines of code. `set -euo pipefail` everywhere. Tier-aware via `.workshop/config.toml`. The 5th hook (post-commit, adversarial review) is managed by [roborev](https://github.com/roborev-dev/roborev) when installed.

### Added — 15 project templates

Static markdown and TOML templates in `templates/` with Jinja2 `{{var}}` placeholders, rendered by `workshop init` against project-specific values.

- Project-level: `CLAUDE.md.starter` (5-rule starter), `plan.md.template`, `HANDOVER.md.template`, `README.md.template`, `AGENTS.md.template`
- Workshop-level: `CLAUDE.md.global` (10 default rules)
- Tier configs: `framework.config.toml.production`, `.standard`, `.sketch` (reflecting spec §14 defaults)
- Learning module: side-quests, skills-log, comprehension-audits, ratio-log (empty), weekly-digest
- Tier-selection ADR: `0001-tier-selection.md.template`

### Added — design + documentation

- Full design specification at `docs/spec.md` (~2000 lines, 18 sections)
- 1-page architecture summary at `docs/architecture.md`
- First ADR: tiers as risk profiles, not project categories
- 5-rule starter `CLAUDE.md` (production tier)
- Dogfooded `plan.md` (Joinery's own build plan)
- Minimal OSS hygiene: CONTRIBUTING, SECURITY
- `.gitattributes` for cross-platform LF normalization

### Known limitations

- `workshop setup` not yet implemented (the doctor reports `~/.config/joinery/ MISSING` and tells you to run setup; the command lands when first needed)
- External sync adapter pattern is spec'd but no skeleton ships yet
- No GitHub Actions CI workflow; lint + typecheck + tests run locally only
- Cross-platform CI testing deferred — Windows verified, Linux relies on pure stdlib + click + jinja2 portability
- Deeper audit of `obra/superpowers` deferred to first real dogfood

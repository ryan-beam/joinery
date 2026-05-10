# Changelog

All notable changes to Joinery are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 3 — Hooks (2026-05-10)

4 git hook bash scripts that `workshop init` will install into `.git/hooks/` of scaffolded projects. The 5th hook (post-commit, for adversarial review) is managed by roborev, not Joinery.

- `pre-commit` — lint + type-check on staged files; AGENTS.md mirror from CLAUDE.md; tier-aware (type-check only on production)
- `pre-push` — refuses direct main pushes on production tier; reads `reviews/` for critical findings and refuses if any open
- `commit-msg` — enforces Lore Protocol structure on production-tier commits over threshold; bypasses trusted bot authors
- `post-merge` — surfaces post-merge actions; quick lint check without auto-fix

Implementation principles applied:
- `set -euo pipefail` at top of every script
- Specific error messages naming the rule violated and pointing to docs
- Tier-aware via `.workshop/config.toml` (read via Python tomllib in one call per hook)
- Per-hook toggles respected (each hook checks its `[hooks].<name>` flag)
- Cross-platform: `python3` with `python` fallback for Windows Git Bash compatibility
- All hooks executable (chmod +x)

Each hook is under 50 lines of code (excluding comments and blank lines).

### Phase 2 — Skills (2026-05-10)

23 skill files for the framework's behavioral surface. Auto-invocation triggers explicit in each skill's frontmatter. Most skills auto-invoke from natural language; three are manual-only by design (`/rule`, `/audit`, `/security-review`); several are hook-fired or composed by other skills.

- **Planning skills (6):** `plan` (orchestrator, leverages Claude Code plan mode), `plan-system`, `plan-data`, `plan-flows`, `plan-decisions`, `plan-side-quests`
- **Workflow skills (7):** `mark` (failing tests from plan), `explain-back`, `handover`, `review` (adopts Claude Code built-in / roborev / fallback), `security-review` (manual; adopts built-in or deep_reviewer), `adr`, `pr`
- **Discipline skills (4):** `rule` (Hashimoto pattern, manual only), `sq`, `audit` (manual + cadence-prompted by digest), `digest`
- **Documentation skills (4):** `docs` (orchestrator), `docs-changelog`, `docs-getting-started`, `docs-architecture`
- **Session skills (2):** `workshop-session-start`, `workshop-session-end`

Audit-first applied: Claude Code already ships `/review` and `/security-review` as built-in skills, so Joinery's versions become thin wrappers (engine priority: roborev > Claude Code built-in > Claude subprocess fallback). Deeper audit of `obra/superpowers` deferred to Phase 5 dogfooding when real friction will surface what to fork.

Skill count cuts: 25 → 23 by dropping `/plan-contracts` (tests are the contract; `/mark` and `/plan-data` cover) and `/plan-risks` (folded inline into Approach via `/plan-system`).

### Phase 1 — Project Templates (2026-05-10)

Static markdown and TOML templates that `workshop init` will copy into new projects (Phase 4 wires this up). Phase 1 is content-only; no Python or bash logic.

- Project-level templates: `CLAUDE.md.starter`, `plan.md.template`, `HANDOVER.md.template`, `README.md.template`, `AGENTS.md.template`
- Workshop-level template: `CLAUDE.md.global` (10 default rules from spec §11)
- Tier config variants: `framework.config.toml.production`, `.standard`, `.sketch` (reflecting spec §14 defaults)
- Learning module templates: `side-quests`, `skills-log`, `comprehension-audits`, `ratio-log.jsonl`, `weekly-digest`
- Tier-selection ADR template: `docs/decisions/0001-tier-selection.md.template`
- Templating syntax: Jinja2-style `{{var}}` placeholders (`{{project_name}}`, `{{tier}}`, `{{language}}`, `{{init_at}}`, `{{joinery_version}}`, `{{date}}`)

### Phase 0 — Foundation (2026-05-10)

Initial repository structure. Phase 0 is structure-only; no executable code yet. The framework runs on production tier from day one and eats its own dogfood.

- Repository skeleton per spec §5 (Project Layout)
- Full design specification at `docs/spec.md`
- 1-page architecture summary at `docs/architecture.md`
- First ADR: tiers as risk profiles, not project categories
- 5-rule starter `CLAUDE.md` (production tier)
- AGENTS.md mirror of CLAUDE.md (manual until pre-commit hook lands in Phase 3)
- Dogfooded `plan.md` for the v1 build
- pyproject.toml skeleton with hatchling backend (workshop CLI lands in Phase 4)
- Placeholder READMEs in `templates/`, `skills/`, `hooks/`, `src/joinery/`, `tests/` documenting which build phase fills each
- `.gitattributes` for cross-platform LF normalization
- Minimal OSS-readiness: CONTRIBUTING, CHANGELOG, SECURITY

Subsequent phases will be logged here as they ship.

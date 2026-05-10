# Changelog

All notable changes to Joinery are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

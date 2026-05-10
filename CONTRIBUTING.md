# Contributing to Joinery

Joinery is in **v1 build phase**. The framework is being constructed across 6 phases (see [`plan.md`](plan.md)). Major contributions are likely blocked until v1 ships and the framework can be dogfooded against real production work.

That said, contributions in these forms are welcome:

- **Bug reports** — open an issue using the bug template
- **Design feedback** — open a discussion or feature-request issue about specific spec sections
- **Documentation fixes** — typos, broken links, unclear prose; small PRs welcome
- **Audit suggestions** — if there's an existing tool/skill that would let Joinery delete custom code (per the Adopt > Fork > Build discipline in [`docs/spec.md`](docs/spec.md) §15), please surface it

## Dev setup

Requires Python 3.11+.

```bash
git clone https://github.com/ryan-beam/joinery
cd joinery
pip install -e ".[dev]"
```

This installs the package in editable mode plus dev dependencies (pytest, ruff, mypy).

## Code style

The framework eats its own dogfood. All code passes:

- `ruff check` (lint)
- `ruff format --check` (format)
- `mypy --strict` (types)
- `pytest` (tests, when they exist; Phase 4 onward)

These are checked in CI on every PR. Failure blocks merge.

The full code style is documented in the workshop-level CLAUDE.md (eventually shipped at `~/.config/joinery/CLAUDE.md`). For now see [`docs/spec.md`](docs/spec.md) §11 for the 10 default rules — no emojis in code, descriptive names, ISO 8601 dates, UTC times, comments earn their place, etc.

## Commit format

Commits to this repo follow the Lore Protocol-flavored format described in [`docs/spec.md`](docs/spec.md) §13. Below the threshold (10 lines changed), a one-liner is fine:

```
<scope>: <one-line summary>
```

Above the threshold, the full body is expected:

```
<scope>: <one-line summary>

context: <one paragraph>
considered: <alternatives>
rejected because: <why>
decided: <chosen approach>
ref: <plan.md section, ADR, etc.>
```

## PR process

1. Branch from `main`. Branch name: `<type>/<short-summary>` where type is `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, or `perf`.
2. Make changes in the branch. Each commit follows the format above.
3. Open a PR. The PR description should follow the Lore Protocol body — the PR template helps.
4. CI runs on the PR (ruff + mypy). Fix any failures.
5. Review and merge. Default is squash-merge; the PR description becomes the squash commit body.

## Where to ask questions

- GitHub Issues for bugs and feature requests
- GitHub Discussions for design questions and broader conversation (when enabled)

## What this project will NOT accept

- Code that bypasses production-tier discipline (see [`docs/spec.md`](docs/spec.md) §4)
- Features beyond the v1 spec scope without surfacing first via a discussion or feature-request issue
- Theoretical rules added to CLAUDE.md (see [`docs/spec.md`](docs/spec.md) §11 — rules grow from real failures)
- Personal-context references in framework code or templates

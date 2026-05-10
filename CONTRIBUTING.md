# Contributing to Joinery

Joinery is at **v0.1.0** — pre-alpha. The framework is functionally complete but unbattle-tested. Expect breaking changes pre-v1.0 as scars from real-world dogfooding accumulate.

Contributions welcome in these forms:

- **Bug reports** — open an issue with reproduction steps
- **Design feedback** — open a discussion (or feature-request issue) about specific spec sections
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

Verify:

```bash
workshop --version    # 0.1.0
ruff check .          # clean
ruff format --check . # clean
mypy                  # no errors
pytest                # 42 tests pass
```

## Code style

The framework eats its own dogfood. All code passes:

- `ruff check` (lint)
- `ruff format --check` (format)
- `mypy --strict` (types)
- `pytest` (tests)

The full code style is documented in the workshop-level CLAUDE.md (`templates/CLAUDE.md.global`, installed at `~/.config/joinery/CLAUDE.md`). Key rules: no emojis in code or configs, comments earn their place, descriptive names, ISO 8601 dates, UTC times, forward slashes in paths. See [`docs/spec.md`](docs/spec.md) §11 for the full list.

## Commit format

Commits to this repo follow the Lore Protocol-flavored format described in [`docs/spec.md`](docs/spec.md) §13. Below 10 lines changed, a one-liner is fine:

```
<scope>: <one-line summary>
```

Above 10 lines, the full body is expected:

```
<scope>: <one-line summary>

context: <why this change>
considered: <alternatives>
rejected because: <why>
decided: <chosen approach>
ref: <plan.md section, ADR, etc.>
```

## PR process

1. Branch from `main`. Branch name: `<type>/<short-summary>` where type is `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, or `perf`.
2. Make changes in the branch. Each commit follows the format above.
3. Open a PR. The PR description follows the Lore Protocol body.
4. Fix any review findings.
5. Squash-merge. The PR description becomes the squash commit body.

## Where to ask questions

- GitHub Issues for bugs and feature requests
- GitHub Discussions for design questions and broader conversation (when enabled)

## What this project will NOT accept

- Code that bypasses production-tier discipline (see [`docs/spec.md`](docs/spec.md) §4)
- Features beyond the v1 spec scope without surfacing first via a discussion or feature-request issue
- Theoretical rules added to CLAUDE.md (see [`docs/spec.md`](docs/spec.md) §11 — rules grow from real failures, not theory)
- Personal-context references in framework code or templates

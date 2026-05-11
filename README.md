# Joinery

> A personal coding framework for the AI-agent era.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python: >=3.11](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)
![Typed: mypy strict](https://img.shields.io/badge/typed-mypy%20strict-blue.svg)
![Status: pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)

Joinery is a system of files, skills, hooks, and conventions installed into projects via `workshop init`. It composes load-bearing patterns from rigorous practitioners — McKinney, Karpathy, Willison, Howard, Hashimoto, Litt, Beck, Anthropic — into a single workflow for designing, shipping, and **understanding** reliable software with strong agent leverage.

AI lets you ship faster but makes it easy to stop understanding what you ship. The Anthropic agentic-coding RCT measured a 17% comprehension decline in AI-assisted developers. Joinery exists to keep AI leverage without becoming a passenger.

---

## Install

Joinery is in pre-alpha. From source:

```bash
git clone https://github.com/ryan-beam/joinery
cd joinery
pip install -e ".[dev]"
```

`pip install` exposes a `workshop` command globally. When the framework stabilizes, `pipx install joinery-cli` will work.

## Quickstart

```bash
workshop init my-project --tier production --lang python
cd my-project
workshop session start
```

`workshop init` scaffolds a complete project: `CLAUDE.md` with the 5-rule starter, a Mermaid-ready `plan.md`, the learning module (`learning/`), git hooks for lint/types/tests, and an opinionated `framework.config.toml` tuned to your tier. `workshop session start` runs preflight, surfaces open side quests, and orients you for the work session.

### Adopting Joinery into an existing project

```bash
cd my-existing-project
workshop adopt --tier production --lang python
git status                # review the new files
git add -A && git commit -m 'joinery: adopt framework'
```

`workshop adopt` overlays the framework onto a codebase that already exists. It is **non-destructive** by default — any file already present (your `README.md`, your `CLAUDE.md`, etc.) is preserved and reported; only missing files are written. Pass `--force` to overwrite. Adopt does not auto-commit; you stage and review the changes through your normal git flow.

Before writing anything, `adopt` runs a **safety scan**: refuses on a dirty working tree (override with `--allow-dirty`), warns about sensitive paths like `.env` or `*.pem`, warns when other hook managers (husky, lefthook, pre-commit framework) are present, and backs up any existing git hooks to `.joinery/backup/hooks-<timestamp>/` before installing its own. Pass `--no-scan` to disable.

Both `init` and `adopt` write a `.workshop/answers.toml` file recording what Joinery installed (version, tier, language, managed files, preserved files, hooks). That answer file is the foundation for future `workshop diff` / `workshop update` flows — it's how Joinery remembers what it manages in your repo.

Add `--dry-run` to either `init` or `adopt` to preview the operation without writing anything. Every real run records a transaction at `.joinery/transactions/<timestamp>.json`; `workshop rollback` undoes the most recent transaction (deletes the files it wrote, restores any hook backup).

`workshop diff` shows drift between your project's managed files and Joinery's current templates (read-only); `workshop update` applies it (with confirmation, plus `--dry-run` for preview). Only files Joinery wrote are touched — your edits to preserved files are never affected.

Run `workshop --help` to see all subcommands (`init`, `adopt`, `rollback`, `diff`, `update`, `session`, `promote`, `doctor`).

## What's in the box

| Layer | What it does |
|---|---|
| **5-phase workflow** | Sharpening → Drafting → Marking → Cutting → Finishing. The work rhythm. |
| **3 tiers** | `production` / `standard` / `sketch` — risk profiles, not project sizes. A 50-line script touching prod payments is production tier. |
| **23 composable skills** | Auto-invoke from natural language for most. `/plan` orchestrator leverages Claude Code plan mode. |
| **4 git hooks** | Lint + type-check pre-commit; refuse direct main pushes pre-push (production); Lore Protocol structure on commit-msg; preflight on merge. |
| **Adversarial review** | Writer ≠ reviewer pattern. Adopts [roborev](https://github.com/roborev-dev/roborev) when installed; falls back to Claude Code's built-in `/review`. |
| **Learning module** | `learning/side-quests.md`, `skills-log.md`, `comprehension-audits.md`, `ratio-log.jsonl`, `weekly-digests/`. Defends comprehension over time. |
| **Documentation system** | `docs/` paired with git history. WHAT and HOW lives in docs; WHEN and WHY lives in commit log. |
| **External sync adapter** | Optional outbound integration to your personal dashboard, Notion, Slack, etc. User supplies the script; framework provides the hook. |

## Philosophy

Three frames sit underneath every design choice:

1. **Comprehension is the load-bearing skill in the AI era.** You can become an orchestrator (good); you must never become a passenger (bad).
2. **Carpentry as a real metaphor, not decoration.** Measure twice cut once. Sharp tools make safe work. Joinery is invisible when done right. Each principle maps to a concrete mechanism in the framework.
3. **Learn-first, ship-second — but still ship production.** AI is allowed to expand the *scope* of what you attempt, not skip understanding what you build.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — 1-page system overview
- [`docs/spec.md`](docs/spec.md) — full design specification (~2000 lines, 18 sections)
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records
- [`plan.md`](plan.md) — the dogfooded v1 build plan (Joinery's own plan, written using its own template)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev setup, code style, PR process

## Status

**v0.1.0 — pre-alpha.** The complete v1 framework: templates, skills, hooks, and the workshop CLI. Built from a 2000-line design specification and dogfooded on itself. Expect breaking changes pre-v1.0 as friction from real-world use surfaces. See [`CHANGELOG.md`](CHANGELOG.md).

## License

[MIT](LICENSE).

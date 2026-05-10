# Joinery

A personal coding framework for the AI-agent era.

## What it is

Joinery is a system of files, skills, hooks, and conventions that lives in a repo and gets installed into projects via `workshop init`. It composes load-bearing patterns from rigorous practitioners — McKinney, Karpathy, Willison, Howard, Hashimoto, Litt, Beck, Anthropic — into a single workflow for designing, shipping, and **understanding** reliable software with strong agent leverage.

It is not a library. It is not a tool in the conventional sense. It is the workshop and the rules of the workshop.

## Why it exists

AI lets you ship faster, but it makes it easy to stop understanding what you ship. The Anthropic agentic-coding RCT measured a 17% comprehension decline in AI-assisted developers. Joinery exists to keep AI leverage without becoming a passenger — to expand the scope of what you can attempt without skipping the understanding of what you build.

The carpentry metaphor is load-bearing, not decoration. Measure twice cut once. The right tool for the job. Sharp tools make safe work. Joinery is invisible when done right. Learn alongside masters. Each principle maps to a concrete framework mechanism.

## Status

**v1 in build.** The specification is complete (see [`docs/spec.md`](docs/spec.md)). The build is sequenced across 6 phases (see [`plan.md`](plan.md)).

- Architecture summary: [`docs/architecture.md`](docs/architecture.md)
- Full design spec: [`docs/spec.md`](docs/spec.md)
- Build plan: maintained externally during development; see commits for progress
- Decisions: [`docs/decisions/`](docs/decisions/)

## Architecture in one paragraph

Five phases (Sharpening, Drafting, Marking, Cutting, Finishing) give projects a work rhythm. Three tiers (production, standard, sketch) are risk profiles, not project categories. Skills compose: a `/plan` orchestrator pulls in sub-skills for the planning phase. Git hooks fire at commit, push, and merge — deterministic where possible, agent-driven only when needed and cost-gated. Every artifact lives in git: `plan.md`, ADRs, `learning/side-quests.md`, `CLAUDE.md` rules accumulated as scars from real failures. The framework is the product. The walls matter more than the model.

## How to install (once v1 ships)

```
pipx install joinery-cli
workshop init my-project --tier production --lang python
cd my-project
workshop session start
```

The CLI binary is `workshop`. Distinguishes from `joinery` the framework — the workshop is what you use, the joinery is what you build.

## Repository layout

```
joinery/
├── README.md           # this file
├── LICENSE             # MIT
├── CLAUDE.md           # this project's own rules (5-rule starter)
├── AGENTS.md           # mirror of CLAUDE.md (Cursor/Codex compatibility)
├── plan.md             # the v1 build plan, dogfooded on itself
├── docs/
│   ├── README.md       # docs index
│   ├── architecture.md # 1-page architecture summary
│   ├── spec.md         # full design specification
│   └── decisions/      # ADRs
├── templates/          # markdown templates installed by workshop init (Phase 1)
├── skills/             # skill files (Phase 2)
├── hooks/              # git hook scripts (Phase 3)
├── src/joinery/        # Python CLI source (Phase 4)
├── tests/              # CLI tests (Phase 4)
└── pyproject.toml      # package metadata
```

## License

MIT. See [`LICENSE`](LICENSE).

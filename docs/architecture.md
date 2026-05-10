# Architecture

Joinery in one page. For the full design rationale, see [`spec.md`](spec.md).

## What it is

A composition of files, skills, hooks, and conventions installed into projects via `workshop init`. Not a runtime — a system of artifacts that lives in a repo and gets copied into projects.

## Five phases of work

The work rhythm. Every meaningful project cycles through these in order:

1. **Sharpening** — `workshop init` scaffolds the project
2. **Drafting** — `plan.md` written through unbounded conversation (leverages Claude Code plan mode when available)
3. **Marking** — `/mark` translates plan success criteria into failing tests
4. **Cutting** — agent implements; human directs at higher abstraction
5. **Finishing** — explain-back, ADR if warranted, HANDOVER, adversarial review

## Three tiers

Risk profiles, not project categories. A 50-line bash script that touches production payments belongs in production tier.

- **Production** — real users, real money, real consequences. Full rigor, all gates required.
- **Standard** — personal serious projects. Most gates advisory.
- **Sketch** — throwaways. Just the non-negotiables (learning module + comprehension never optional).

## Composable skills

23 markdown files in `skills/` that shape agent behavior. Auto-invoked from natural language (most), hook-fired (some), reserved for manual invocation (`/rule`, `/audit`, `/security-review`).

Skill catalog:
- 6 planning skills (`/plan` orchestrator + sub-skills)
- 7 workflow skills (`/mark`, `/explain-back`, `/handover`, `/review`, `/security-review`, `/adr`, `/pr`)
- 4 discipline skills (`/rule`, `/sq`, `/audit`, `/digest`)
- 4 documentation skills (`/docs` orchestrator + sub-skills)
- 2 session skills (`workshop session start`, `workshop session end`)

## Tier-aware hooks

4 git hooks managed by Joinery, plus 1 managed by roborev (post-commit adversarial review):

- `pre-commit` — lint + type-check + test + CLAUDE.md → AGENTS.md mirror
- `pre-push` — last-line-of-defense; refuses direct main pushes on production tier
- `commit-msg` — Lore Protocol structure check; bot/daemon authors bypass
- `post-merge` — preflight refresh

Each hook reads `framework.config.toml` to know the tier and enabled features.

## Documentation as spine partner

Git history covers WHEN and WHY (chronological record). `docs/` covers WHAT and HOW (current state, navigable). Together they're the project's record.

## Learning module

`learning/` directory captures comprehension-defense artifacts:
- `side-quests.md` — concepts you don't fully grok yet
- `skills-log.md` — concepts you DO understand now
- `comprehension-audits.md` — weekly cold-explanation ritual
- `ratio-log.jsonl` — primary/secondary tracking per session
- `weekly-digests/` — generated digests, archived

Toggleable but on by default — the framework's strongest non-negotiable.

## External integrations

- **roborev** — adopted as the adversarial review engine (Go tool, multi-agent, runs locally). Joinery integrates; doesn't re-implement. Graceful fallback if missing.
- **ccstatusline** — adopted as the v1 statusline default. One-time global setup.
- **Optional sync adapter** — framework provides the hook; user supplies the script that POSTs/writes to their personal system.

## Configuration

`framework.config.toml` is the per-project knob set. Tier defaults are starting points; everything is overridable per-feature.

## Where to learn more

- Full design spec: [`spec.md`](spec.md)
- Per-decision ADRs: [`decisions/`](decisions/)
- Build phases and progression: [`../plan.md`](../plan.md)

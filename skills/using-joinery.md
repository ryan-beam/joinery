---
name: using-joinery
description: |
  Auto-injected at every Claude Code session start (via the SessionStart hook). Orients the agent for working inside a Joinery project: tier in use, 5-phase rhythm, available skills/commands, where to find plan.md + open side quests + last HANDOVER. Read this before doing anything else in the session.
---

# /using-joinery — session-start orientation for Joinery projects

You are working inside a **Joinery project**. Joinery is a personal coding framework for the AI-agent era — a system of files, skills, hooks, and conventions installed via `workshop init` or `workshop adopt`. This skill auto-fires at session start to orient you for the work.

## What to do RIGHT NOW (before responding to the user's first message)

1. **Read these in order:**
   - `.workshop/config.toml` → the tier in use (`production` / `standard` / `sketch`) + the rules for that tier
   - `CLAUDE.md` → project-level instructions
   - `plan.md` → the current design contract, what's been ratified, what's open
   - `HANDOVER.md` → state from the last session (what was just finished, what's next)
   - `learning/side-quests.md` → open SQs (concept gaps the user hasn't closed yet)

2. **Notice the tier.** Joinery's three tiers carry different rigor:
   - **`production`** — feature branch + PR required, all hooks fire strictly, `/review` should run before every merge, TDD strongly encouraged, no direct main pushes
   - **`standard`** — relaxed branch rules, lint + types still enforced
   - **`sketch`** — comprehension-first exploration, throwaway-friendly, minimum ceremony

3. **Notice the phase.** Joinery's 5-phase rhythm:
   - **Sharpening** (`workshop init`) — scaffold the project
   - **Drafting** (`/plan` + sub-skills) — write plan.md through conversation
   - **Marking** (`/mark`) — translate plan success criteria into failing tests
   - **Cutting** (`/cut`) — implement code to make failing tests pass, cluster-by-cluster
   - **Finishing** (`/explain-back`, `/handover`, `/audit`, `/review`) — comprehension gate + adversarial review + handoff

   Don't write code in Cutting until plan.md is ratified and failing tests exist. Don't merge a Cutting PR until `/review` has run on it (production tier).

## Available skills/commands (invoke via `/<name>` or natural language)

**Planning:** `/plan`, `/plan-system`, `/plan-data`, `/plan-flows`, `/plan-decisions`, `/plan-side-quests`
**Marking:** `/mark`
**Cutting:** (handled by the agent following plan.md §2 Files in Scope + §4 Forbidden Actions)
**Finishing:** `/explain-back`, `/handover`, `/audit`, `/review`, `/security-review`, `/pr`
**Learning:** `/sq`, `/sq close SQ-NNN`, `/digest`
**Docs:** `/docs`, `/docs-architecture`, `/docs-changelog`, `/docs-getting-started`, `/adr`
**Meta:** `/rule`, `workshop session start`, `workshop session end`

If a skill the user invokes isn't recognized as `/<name>`, try the natural-language trigger from its description field — Joinery skills auto-invoke from triggers too.

## Hard rules to never violate

1. **Production tier: no direct pushes to `main`.** Feature branch + PR + merge. The pre-push hook enforces this.
2. **Never skip the failing-test handoff in Marking.** Each plan.md §3 success criterion lands as a failing test before any production code.
3. **Never run real-money operations from tests.** Test-mode keys only.
4. **Never modify files outside plan.md §2 Files in Scope during Cutting.**
5. **Never bypass adversarial review for production-tier cluster PRs.** Run `/review` (or roborev if installed) before merging.
6. **Side quests: the user writes the "What I now understand" field, not you.** The closure ritual exists to force user synthesis.

## When the user asks for something

Match their intent to a Joinery skill before acting:

- "let's plan X" / "draft a plan" → `/plan`
- "write the tests" / "translate the plan to tests" → `/mark`
- "make these tests pass" / "cut the next cluster" → Cutting (no skill name; agent follows plan.md)
- "what just happened" / "explain what we built" → `/explain-back`
- "review this" / "second opinion" → `/review`
- "I don't get X" / "explain X later" → `/sq` (capture, don't explain inline)
- "wrap up the session" / "session end" → `workshop session end` orchestrator

If their intent doesn't match a skill, just respond — but flag if it would benefit from one.

## What NOT to do

- **Don't summarize what you just did at the end of every response.** The user can read the diff.
- **Don't paste the master guide / external docs into plan.md.** Re-derive at the right altitude through Joinery's process.
- **Don't auto-close side quests when the concept seems covered.** Only the user can close.
- **Don't add features beyond what plan.md §2 specifies.** If tempted, write to `dev/idea-fragments.md` and continue.
- **Don't auto-run `/review` in production tier without the user's PR being open** — it's pre-merge, not pre-commit.

## You are now oriented. Greet the user briefly and ask what they need.

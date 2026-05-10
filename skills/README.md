# skills/

Markdown skill files that shape agent behavior in scaffolded projects. Each is a small, focused file Claude Code (or other compatible agents) reads at invocation.

## Catalog (23 skills)

**Planning (6):**
- `plan` — orchestrator; drives unbounded planning conversation, leverages Claude Code plan mode
- `plan-system` — architecture sketch with Mermaid
- `plan-data` — ER diagram (conditional)
- `plan-flows` — sequence diagrams (conditional)
- `plan-decisions` — surfaces decisions, drafts ADRs
- `plan-side-quests` — extracts learning gaps to `learning/side-quests.md`

**Workflow (7):**
- `mark` — failing tests from plan success criteria
- `explain-back` — comprehension-gate transcript
- `handover` — session-end state for next session
- `review` — adversarial review (roborev > Claude Code built-in > Claude subprocess fallback)
- `security-review` — security-focused review (manual only)
- `adr` — Architecture Decision Record
- `pr` — Lore Protocol-flavored PR description

**Discipline (4):**
- `rule` — capture a real failure as a CLAUDE.md rule (manual only)
- `sq` — side quest capture
- `audit` — comprehension audit scaffold (manual or cadence-prompted)
- `digest` — weekly digest aggregating SQs, skills logged, ratio, token usage

**Documentation (4):**
- `docs` — orchestrator; surveys staleness, composes sub-skills
- `docs-changelog` — update CHANGELOG from git
- `docs-getting-started` — refresh onboarding doc from current project state
- `docs-architecture` — refresh architecture doc from code + ADRs

**Session (2):**
- `workshop-session-start` — read HANDOVER, run preflight
- `workshop-session-end` — explain-back + handover + SQ reconcile + token report

## Invocation modes

- **Auto-invoke** (most skills) — Claude reads the frontmatter `description` and triggers from natural language
- **Manual only** — `rule`, `audit`, `security-review` (intentionality matters)
- **Hook-fired** — `review`, `explain-back`, `handover`, `mark`, `plan-decisions`, `plan-side-quests` (triggered by hooks or composed by other skills)

See `docs/spec.md` §7 (Skill Catalog) for full per-skill design.

## Skill file format

```yaml
---
name: <skill-name>
description: <one paragraph including explicit trigger phrases>
---

# <Skill Name>

## When to use
<one paragraph>

## Procedure
<numbered steps>

## Output format
<what to produce>

## Examples
<1-2 worked examples>
```

The frontmatter `description` field is load-bearing — Claude matches natural language against it to decide when to auto-fire the skill.

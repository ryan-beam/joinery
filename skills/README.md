# skills/

The 23 markdown skill files that ship with Joinery. Filled in **Phase 2** of the build.

## What lives here (after Phase 2)

**Planning skills (6):**
- `plan.md` (orchestrator)
- `plan-system.md`, `plan-data.md`, `plan-flows.md`
- `plan-decisions.md`, `plan-side-quests.md`

**Workflow skills (7):**
- `mark.md`, `explain-back.md`, `handover.md`
- `review.md`, `security-review.md` (thin wrappers around roborev)
- `adr.md`, `pr.md`

**Discipline skills (4):**
- `rule.md`, `sq.md`, `audit.md`, `digest.md`

**Documentation skills (4):**
- `docs.md` (orchestrator)
- `docs-changelog.md`, `docs-getting-started.md`, `docs-architecture.md`

**Session skills (2):**
- `workshop-session-start.md`, `workshop-session-end.md`

## Skill file format

Each skill is a markdown file Claude Code reads at invocation. Frontmatter declares name + description (used for auto-invocation matching). Body declares procedure, output format, examples.

```yaml
---
name: <skill-name>
description: <when to invoke; explicit trigger phrases>
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

## Phase 2 audit-first discipline

Before writing any skill from scratch, check existing options:
1. Claude Code built-in skills
2. `obra/superpowers` skill pack
3. Other community skills

Only write from scratch what has no existing fit. Final skill count may be lower than 23 if audits succeed.

See [`../docs/spec.md`](../docs/spec.md) §7 (Skill Catalog) for the full skill list with triggers and costs. See [`../plan.md`](../plan.md) §3 for Phase 2 success criteria.

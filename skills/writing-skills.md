---
name: writing-skills
description: |
  Author a new Joinery skill. TDD-style workflow for skill authoring: state the trigger phrases, write the skill markdown, dry-run it, dogfood it, then ship. Adapted from obra/superpowers writing-skills, but tied to Joinery's 5-phase rhythm and 3-tier system. Triggers when user says "write a new skill", "author a skill", "add a /<name> skill", "let's create a skill for X", "skill for handling Y".
---

# /writing-skills — author a new Joinery skill

## When to use

Two cases:

1. Adding a new skill to Joinery's surface area — lands in `skills/<name>.md` in this repo, ships in the next release.
2. Adding a project-local skill via `workshop adopt` to a non-Joinery project — lands in `.claude/skills/<name>.md` + `.claude/commands/<name>.md` for that project only.

If the skill is one-off and project-specific, prefer project-local. If it's a discipline you want everywhere, it belongs in Joinery proper.

## The load-bearing principle: skills are contracts, not documentation

Skills are read by agents at runtime. Every line affects behavior. Treat them as code, not docs.

The TDD analog for skill authoring: **state what triggers the skill, state what it produces, write the skill, then dogfood by actually invoking it before merging.** A skill that hasn't been invoked at least once is unverified, same as code that hasn't been run.

## Anatomy of a Joinery skill

Every skill has the same five-part shape:

1. **Frontmatter** — `name` (matches filename), `description` (load-bearing — drives auto-discovery and the slash command). Optional fields as needed.
2. **`When to use`** — which phase, which tier, which scenario. Should be specific enough that the agent doesn't have to guess.
3. **The load-bearing principle** — one sentence stating the discipline the skill enforces. If you can't write this in one sentence, the skill isn't ready.
4. **Procedure** — numbered steps, each with stop conditions where appropriate.
5. **Hard rules** — invariants the skill must never violate.

Optionally: **Pattern origin** — cite the source if ported from obra/superpowers or elsewhere. Future-you needs to know what's ported vs. original.

## Skill-authoring workflow (the TDD analog)

### Step 1 (RED) — Write the description + trigger phrases

Write the frontmatter `description` first. Inside it, list the trigger phrases verbatim — these drive auto-discovery.

**Test it before continuing:** read your own description cold. Would those triggers fire for the use case you intend? Would they fire for things you DON'T want them to fire for? Wrong triggers = skill never fires, OR skill fires when it shouldn't and you waste a session debugging why the agent kept invoking it.

**Stop condition:** you can predict, with confidence, which user phrases will and won't invoke this skill.

### Step 2 (GREEN) — Write the procedure

Write the numbered steps. Each step should be unambiguous to an agent reading the skill cold — no implicit context from your head.

Production-tier skills get stop conditions on multi-step procedures. ("Continue to step 3 only if X.") Without stop conditions, agents drift.

**Stop condition:** an agent who has never seen this skill could execute it correctly.

### Step 3 (REFACTOR) — Read your own skill cold

Open a fresh session. Paste the skill content. Does it tell you what to do? Where does it leave you guessing? Tighten those spots.

Common drift points:
- Steps that assume the agent knows what file to edit
- Tier behavior that's implicit instead of stated
- Stop conditions phrased as suggestions ("you might want to") instead of gates ("don't continue until")

**Stop condition:** zero places where you find yourself adding context in your head that isn't in the skill.

### Step 4 (DOGFOOD) — Invoke the skill in a real Joinery project

Don't ship a skill you haven't invoked. Use it in an actual session on an actual project. Note every place you (the user) had to override or correct what the agent did with the skill loaded.

Each override = a missing line in the skill.

**Stop condition:** the skill runs in a real session without you correcting it.

### Step 5 (SHIP) — Three clean dogfoods

Once 3 consecutive dogfoods need zero correction, the skill is shippable. Commit, PR, merge into the next release.

Three is the threshold because two clean runs can be coincidence; three is a pattern.

## Where skills live

Three locations, three different scopes:

- **Joinery-built skills** → `skills/<name>.md` in this repo. Distributed via `workshop init` / `workshop adopt`.
- **Project-local skills** → `.claude/skills/<name>.md` AND `.claude/commands/<name>.md` (dual-mount, per PR #14). Lives only in that project.
- **User-global skills** → `~/.claude/skills/<name>.md`. Cross-project, your personal toolkit. Not version-controlled with any project.

If you're writing one for Joinery proper, it goes in the first location and gets distributed when projects upgrade.

## Naming conventions

- **kebab-case filename** — `execute-plan.md`, not `executePlan.md` or `execute_plan.md`.
- **`name:` frontmatter matches filename** without the `.md`. The slash command auto-derives from this.
- **Orchestrator skills get verbose names** — `workshop-session-end`, `plan-side-quests`. Signals "this composes other skills."
- **Frequently-invoked skills get short names** — `tdd`, `pr`, `mark`, `cut`. Signals "you'll type this a lot."

If you're torn between long and short, ask: will the user type this name 5+ times per session? If yes, short.

## Tier discipline

A new skill SHOULD declare its tier behavior in the `When to use` section, especially if behavior diverges by tier (like `/tdd` or `/swarm`).

Phrase it explicitly:

> **production tier:** mandatory before merge.
> **standard tier:** recommended.
> **sketch tier:** off by default; invoke manually if useful.

Implicit tier behavior is one of the most common skill bugs — the agent applies sketch-tier latitude to a production-tier project, and the user has to course-correct. Don't make them.

## Common mistakes

- **Verbose preamble before the procedure.** Every line is read by agents at runtime. Wasted tokens, every invocation.
- **Trigger phrases that overlap with another skill.** Causes ambiguous auto-discovery. Before adding a trigger, grep existing skills for it.
- **Missing stop conditions on multi-step procedures.** Agents drift. Production-tier skills especially need them.
- **Implicit tier behavior.** Always be explicit on production-vs-standard-vs-sketch, especially when they diverge.
- **Pattern-origin citations missing.** Future-you needs to know what was ported vs. original. Six months from now you won't remember.
- **Skill that hasn't been invoked.** Untested code. Don't merge.

## Hard rules

- **Frontmatter `description` field is load-bearing.** It drives auto-discovery AND the slash command. Write it deliberately.
- **Trigger phrases must be specific.** Generic triggers ("help me", "do the thing") cause cross-skill collisions.
- **Every procedural step on production-tier skills should have a stop condition.** Otherwise the agent drifts past it.
- **The skill must be read cold AND invoked at least once before shipping.** A skill that hasn't been used is unverified.
- **Three consecutive clean dogfoods before merging into Joinery proper.** One run could be luck; three is a pattern.

## Pattern origin

Adapted from obra/superpowers `writing-skills`. Differences from upstream:

- **Tier-gating** — Joinery's three tiers mean skills must declare their behavior per-tier; upstream is universal.
- **5-phase awareness** — skills are tagged by phase (Sharpening / Drafting / Marking / Cutting / Finishing); upstream has no phase concept.
- **Dual-mount file locations** — Joinery skills exist at both `.claude/skills/` (auto-discovery) and `.claude/commands/` (explicit slash command); upstream uses skills-only after v5.1.0 deprecation.

The TDD-for-skills loop (RED → GREEN → REFACTOR → DOGFOOD → SHIP) is direct from upstream, with the dogfood step elevated because Joinery's "first real use" discipline applies to skills the same way it applies to features.

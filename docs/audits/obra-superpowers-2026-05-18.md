# obra/superpowers Audit vs. Joinery v0.1.5

**Date:** 2026-05-18
**Auditor:** background research agent dispatched from Joinery's first dogfood (placket-ops build)
**Verdict:** 8 PORT, 4 SKIP, 2 REJECT — audit was worth doing, foundational patterns identified
**Closes:** the deferred audit referenced in `docs/spec.md` §11.4 + §11.5 and state.md line 545

---

## Why this exists

Joinery's design spec explicitly cites `obra/superpowers` as a source to audit and steal/port from. Per spec line 1990 + state.md line 545: **the deeper obra/superpowers audit was deferred to the first real dogfood when friction would surface what to fork.** That dogfood (placket-ops auto-print build) is happening 2026-05-18, friction has surfaced, audit is now complete.

## Section 1: What obra/superpowers actually contains

**Identity.** Superpowers is "a complete software development methodology for coding agents, built on top of a set of composable skills and some initial instructions." Maintained by Jesse Vincent (`obra` / fsck.com). MIT licensed. Multi-platform: ships as a plugin for Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub Copilot CLI, and Factory Droid.

**Activity / maintenance signal.** Highly active. **440 commits on main, latest release v5.1.0 dated 2026-05-04** (two weeks ago).

**Top-level layout.**
- `.claude-plugin/` (plugin.json + marketplace.json — Claude Code plugin manifest)
- `.codex-plugin/`, `.cursor-plugin/`, `.opencode/` (per-platform plugin shims)
- `skills/` (14 skill directories, each with `SKILL.md`)
- `hooks/` (`hooks.json`, `run-hook.cmd`, `session-start` script)
- `scripts/` (`bump-version.sh`, `sync-to-codex-plugin.sh`)
- `tests/`, `docs/`, `assets/`
- `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` (per-agent system instructions)
- `RELEASE-NOTES.md`
- `package.json`, `gemini-extension.json`

**Skill inventory (14 total).**
1. `using-superpowers` — meta-skill, mandates skill discovery at conversation start
2. `writing-skills` — TDD-style workflow for authoring new skills
3. `brainstorming` — pre-implementation design dialogue with hard gate
4. `writing-plans` — produces dated implementation plans at `docs/superpowers/plans/`
5. `executing-plans` — load/review/execute plan with stop conditions
6. `subagent-driven-development` — per-task subagent dispatch with two-stage review
7. `dispatching-parallel-agents` — fan-out independent failures to parallel agents
8. `test-driven-development` — strict RED-GREEN-REFACTOR
9. `systematic-debugging` — 4-phase, "no fixes without root cause"
10. `verification-before-completion` — evidence-must-precede-claims gate
11. `requesting-code-review` — dispatch reviewer subagent, triage by severity
12. `receiving-code-review` — verify-before-acting on feedback
13. `using-git-worktrees` — detect isolation, prefer harness-native, fallback to `.worktrees/`
14. `finishing-a-development-branch` — verify tests → present merge/PR/keep/discard menu

**Hooks.** Exactly one configured hook in `hooks/hooks.json`:
```
SessionStart matcher: "startup|clear|compact"
  → runs hooks/run-hook.cmd session-start (sync)
```
The `session-start` script injects the `using-superpowers` SKILL.md content as `additionalContext` into the new session, so the meta-skill always loads first.

**Setup approach.** Installed as a **plugin** (`/plugin install superpowers@claude-plugins-official` in Claude Code). Skills live in `~/.claude/skills/` (user-global), not `.claude/skills/` (project-local).

**Critical v5.1.0 change:** Slash commands (`/brainstorm`, `/execute-plan`, `/write-plan`) were **explicitly removed**. Skills now invoked exclusively via the `Skill` tool, driven by description-based auto-discovery.

---

## Section 2: Per-skill audit vs. Joinery

| # | obra/superpowers skill | Verdict | Notes |
|---|---|---|---|
| 1 | `using-superpowers` | **PORT (pattern)** | SessionStart hook injecting a meta-skill is a clean pattern Joinery doesn't have. Adapt as `using-joinery`. |
| 2 | `writing-skills` | **PORT (adapted)** | Joinery has no skill-authoring guide. Adapt to reference Joinery's tier system + 5-phase rhythm. |
| 3 | `brainstorming` | **SKIP** | `/plan` + sub-skills cover this and do more. |
| 4 | `writing-plans` | **SKIP** | `/plan` produces plan files. Their template is a convention to borrow for our plan template. |
| 5 | `executing-plans` | **PORT (light)** | Joinery has no stop-condition-driven plan walker. S/M. |
| 6 | `subagent-driven-development` | **PORT (big win)** | Most valuable port. Fresh subagent per task + two-stage review + per-task TodoWrite tracking maps onto cluster PRs. L. |
| 7 | `dispatching-parallel-agents` | **REJECT (for now)** | Premise doesn't match solo cluster-PR work. |
| 8 | `test-driven-development` | **PORT (tier-gated)** | Mandatory in `production`, recommended in `standard`, off in `sketch`. M. |
| 9 | `systematic-debugging` | **PORT (clean win)** | 4-phase RCA workflow is the most "drop-in" port. S. |
| 10 | `verification-before-completion` | **PORT (rule + hook)** | Port as skill + `/rule` entry. S. |
| 11 | `requesting-code-review` | **SKIP, partial port** | Port the **subagent-isolation pattern** into existing `/review`. M. |
| 12 | `receiving-code-review` | **PORT (light)** | Joinery has no review-feedback-triage doc. S. |
| 13 | `using-git-worktrees` | **REJECT** | Conflicts with cluster-PR-on-main + solo rhythm. |
| 14 | `finishing-a-development-branch` | **PORT (as orchestrator)** | Adapt as `workshop session end` orchestrator. L. |

**Summary:** 8 PORT, 4 SKIP, 2 REJECT.

---

## Section 3: Hooks and automation patterns

| Pattern | Verdict | Notes |
|---|---|---|
| **SessionStart hook injecting a meta-skill** | **PORT** | Single highest-leverage automation port. |
| **`run-hook` indirection** | **PORT** | Single dispatcher script for harness-side hooks. S. |
| **Plugin-manifest distribution** | **REJECT** | Conflicts with Joinery's project-local-by-design thesis. |
| **Slash command deprecation (v5.1.0)** | **DO NOT FOLLOW** | Skill auto-invocation is opaque; slash commands are auditable. Keep our slash-command surface. **Dual-mount** to both `.claude/skills/` (auto) and `.claude/commands/` (explicit) — already shipped in PR #14. |

### How obra/superpowers addresses Joinery's 6 known gaps

| Gap | Solved? | Path |
|---|---|---|
| #1 `/review` doesn't auto-fire on cluster PRs | **Yes** — `subagent-driven-development` fires per-task review | Port the auto-review pattern (PR #6 + #8) |
| #2 `/explain-back` is manual | **Partial** — SessionStart hook is the primitive | Port SessionStart, use for nudging |
| #3 `workshop session end` isn't an orchestrator | **Yes** — `finishing-a-development-branch` is exactly this | Port (PR #5) |
| #4 Skills land in wrong dir | **Partial / by deprecation** | Dual-mount (✅ shipped PR #14) |
| #5 `/digest` doesn't auto-fire weekly | **No** | Out of scope; needs scheduler |
| #6 `/sq close` is manual | **No** | Joinery-specific concept |

---

## Section 4: Prioritized porting plan

1. **SessionStart hook + `using-joinery` meta-skill** — S — closes partial #2, foundation
2. **Dual-mount skills** — S — closes #4 — ✅ **SHIPPED PR #14**
3. **`/debug` skill** — S — fills hole
4. **`/verify` skill + rule** — S — indirect
5. **`workshop session end` orchestrator** — L — closes #3
6. **`/review` as isolated subagent** — M — partial #1
7. **`/execute-plan` skill** — M — none direct
8. **`/swarm` skill (subagent-driven-dev)** — L — fully closes #1
9. **Tier-gated `/tdd` skill** — M — raises production bar
10. **`writing-skills` doc + `receiving-review` skill** — S — documentation

---

## Section 5: What to deliberately NOT port

1. **Slash command deprecation.** Joinery's slash commands are auditable, dogfoodable, deliberate UX. Keep them. Dual-mount so both invocation styles work.
2. **`using-git-worktrees`.** Adds ceremony without payoff for solo cluster-PR work.
3. **`dispatching-parallel-agents`.** Premise (≥3 independent failures + multi-agent harness) doesn't match single-builder reality.
4. **Universal TDD as iron law.** Joinery's `sketch` tier exists for comprehension-first exploration. Port TDD as tier-gated rule, not blanket law.
5. **Plugin-as-distribution model.** Joinery is project-local-by-design.
6. **`superpowers:code-reviewer` reviewer subagent** (already removed in v5.1.0). Don't resurrect what their maintainer deprecated.
7. **Cross-platform plugin shims.** Joinery targets Claude Code by design.

---

## Conclusion

Audit was worth doing. Strongest findings:

- **SessionStart hook + meta-skill pattern is the single highest-leverage port.** Cheap, foundational. Do PR #1 first.
- **v5.1.0 slash-command deprecation is a cautionary tale Joinery should explicitly diverge from.** Document the divergence in `docs/spec.md` so future audits don't re-litigate it.

Joinery wins on: tiering, side quests, decision logging, project-local distribution. Joinery loses on: session-startup automation, subagent-isolated review, debugging discipline, branch-finishing orchestrator. The porting plan closes the loss column without touching the wins.

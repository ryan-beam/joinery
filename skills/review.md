---
name: review
description: |
  Run an adversarial code review on the current branch's diff. Engine cascade: roborev (preferred, external process) → isolated Claude Code subagent (via Task tool, fresh context) → Claude Code built-in /review CLI → external `claude code -p` subprocess. Writer-not-equal-reviewer is the load-bearing principle, and isolation from the implementer's reasoning is what makes the review honest. Triggers when user says "review this", "review my code", "review this PR", "give me a second opinion", "check this for bugs", "any issues with this code".
---

# /review — adversarial review

## When to use

Auto-fires on production tier (managed by roborev's post-commit hook if roborev is installed; otherwise invoked by `workshop session end` Phase 4 before a merge). Manually invokable for ad-hoc reviews via the trigger phrases above.

## The load-bearing principle: writer ≠ reviewer

Adversarial review only works if the reviewer is **independent of the implementer's reasoning**. If the reviewer can see the implementer's TODO comments explaining why something looks wrong, the open side quests describing what was deferred, or the conversation that led to the current code, the review gets contaminated. The reviewer ends up *agreeing with the implementer* instead of evaluating the code on its own.

The engine cascade below is ordered by **how strongly isolated the reviewer is from the writer's context** — not just by which tool exists. Roborev wins because it's a separate process with no shared state. The isolated subagent wins second because it has fresh context. The built-in `/review` and the subprocess fallback come after because they offer less isolation.

## Procedure

1. **Detect engine availability** in this priority order:

   **A. roborev (preferred — separate process, full isolation)**
   - Check: `which roborev` or `roborev --version` AND `[review] use_roborev = true` in `framework.config.toml`.
   - If both: `roborev review` for the current diff. Roborev manages its own model selection, prompt, output, and SQLite storage. Findings retrievable via `roborev show <sha> --json`.
   - **Done.** Roborev's separate-process architecture is the strongest available isolation.

   **B. Isolated Claude Code subagent (NEW — fresh-context isolation)**
   - Check: running inside Claude Code AND `[review] use_isolated_subagent = true` in `framework.config.toml` (default true on production + standard, false on sketch).
   - Use the **Task tool** to spawn a fresh subagent with no parent-session context. The subagent receives only:
     - The diff (full `git diff <base>..HEAD` output)
     - The reviewer prompt template (below)
     - The project tier (production / standard / sketch) so severity-grading is calibrated
   - The subagent returns findings as structured markdown. The parent session formats them into `reviews/<sha>.md`.
   - **This is the load-bearing path for projects without roborev** — DO NOT skip to (C) or (D) just because /review is faster in-session. The whole point is that the reviewer has not seen the implementer's reasoning.

   **C. Claude Code built-in `/review` CLI command**
   - If the `/review` slash-command is available in the current Claude Code session AND (B) is disabled or the Task tool isn't available, defer to the built-in.
   - Less isolation: the built-in runs in the current session context, may see prior conversation. Acceptable when (B) isn't viable.

   **D. External `claude code -p` subprocess (last resort)**
   - If none of the above: invoke `claude code -p "<reviewer-prompt>" --model <reviewer-model>` with the diff piped in.
   - Useful when running outside Claude Code entirely (CI, automation, scripted reviews).

2. **Apply cost gate.** Read `[review] min_diff_lines` from config (default 50). Skip review if diff is below threshold. Avoid theater on trivial changes.

3. **Use a different model from the writer.** Read `[review] writer` and `[review] reviewer` from config. If they're the same, surface a configuration warning. (Engine A handles this internally; engines B/C/D consult the config.)

4. **Severity-graded action on findings:**
   - `critical` or `high` → pre-push hook refuses the push; `workshop session end` Phase 4 refuses merge
   - `medium` → logged, no blocking
   - `low` → logged only

## Reviewer prompt template (for engines B and D)

The fresh-context reviewer subagent receives this prompt. Engine D pipes a near-identical version through `claude code -p`. The prompt is deliberately stripped of any context about the implementer's reasoning — that's the isolation discipline.

```
You are an adversarial code reviewer. Your job is to find what's wrong with the
following diff. Read it with a "find what's wrong" mindset — assume the author
got something wrong and your job is to identify it.

You will NOT see:
- The conversation that led to this change
- The implementer's TODO comments or rationale
- The plan.md or open side quests
- Any prior context about WHY decisions were made

This is intentional. Adversarial review must be independent of the writer's reasoning.

PROJECT TIER: <production | standard | sketch>
- production: severity-grade strictly. Data-safety + correctness bugs are critical.
- standard: severity-grade normally. Design smells matter, but only block on real bugs.
- sketch: severity-grade leniently. Exploration code; only flag genuine correctness bugs as critical.

DIFF:
<full git diff output, including file paths and line numbers>

Surface findings in roborev's four-tier severity scale:
- critical = bugs that cause data loss, security holes, contract violations, money-safety failures
- high    = error handling gaps that bite under realistic load, missing validation on user-facing input, race conditions
- medium  = unclear naming, design smells, missing tests, brittle assumptions
- low     = style, formatting, minor inconsistencies (roborev's "nit" tier)

OUTPUT FORMAT:
For each finding:
- `<path/file>:<line>` — <one-sentence description of the issue> [severity]

Group findings by severity. If a severity tier has no findings, write "(none)".
If the entire diff is clean, write "No findings." and stop.

DO NOT:
- Speculate about the implementer's intent
- Suggest improvements that aren't actual bugs (use `medium` for design smells, not `low`)
- Pad with low-severity findings just to look thorough
- Make recommendations the implementer should already know (e.g., "consider adding tests" without saying which test)
```

## Output format (engines B, C, D fallback)

`reviews/<commit-hash>.md`:

```markdown
# Review: <hash>

**Reviewer:** <model>
**Engine:** roborev | isolated-subagent | claude-code-builtin | claude-cli
**Diff:** <N> lines across <M> files
**Time:** <ISO timestamp>

## Critical
- `path/file:line` — <description>

## High
- `path/file:line` — <description>

## Medium
- `path/file:line` — <description>

## Low
- `path/file:line` — <description>
```

The `Engine:` line lets future readers know HOW the review was conducted — important because engines have different isolation guarantees. A review marked `roborev` or `isolated-subagent` has high isolation; one marked `claude-code-builtin` may have been contaminated by in-session context.

## Configuration

```toml
[review]
use_roborev = true                  # Engine A — preferred when available
use_isolated_subagent = true        # Engine B — new in audit PR #6
writer = "claude-sonnet-4-6"
reviewer = "claude-haiku-4-5"       # Engine B/C/D pick from here
deep_reviewer = "claude-opus-4-7"   # For security reviews + high-stakes diffs
min_diff_lines = 50                 # Skip review on tiny diffs
max_diff_lines = 2000               # Refuse to review very large diffs (split first)
auto_fix_scope = "off"              # production: human always in the loop
```

Tier defaults:
- `production` — `use_roborev=true`, `use_isolated_subagent=true`, `auto_fix_scope=off`
- `standard` — `use_roborev=true`, `use_isolated_subagent=true`, `auto_fix_scope=style`
- `sketch` — `use_roborev=false`, `use_isolated_subagent=false`, `auto_fix_scope=all`

Sketch defaults `use_isolated_subagent=false` deliberately — sketch tier is for comprehension-first exploration; the ceremony of spawning isolated subagents fights the iteration speed. If you're sketching and want a review, manually invoke `/review` and the cascade will fall through to (C) or (D).

## Hard rules

- **Engine cascade is ordered by isolation, not convenience.** Do NOT skip from (A) to (C) just because (B) seems heavyweight. The whole framework rests on adversarial review being honest, and honesty requires isolation.
- **The Engine: header in `reviews/<sha>.md` is non-negotiable.** Future readers need to know which engine produced the review so they can weigh the finding accordingly.
- **Reviewer prompt has NO project context beyond tier.** No plan.md, no open SQs, no commit messages, no conversation history. The reviewer sees the code.

## Notes

- Engine priority: roborev > isolated subagent > Claude Code built-in > Claude subprocess fallback
- The fallback exists so the framework keeps working when running outside Claude Code or when roborev is missing
- Engine B (isolated subagent) was added in audit PR #6 — closes the partial fix flagged in `docs/audits/obra-superpowers-2026-05-18.md` for hole #1 (subagent-isolated review)
- See `docs/spec.md` §12 for design rationale and the hedge

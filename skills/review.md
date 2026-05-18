---
name: review
description: |
  Run an adversarial code review on the current branch's diff. Adopts roborev as the preferred review engine, falls back to Claude Code's built-in /review, and as a last resort invokes the agent's reviewer model directly. Writer-not-equal-reviewer is the load-bearing principle. Triggers when user says "review this", "review my code", "review this PR", "give me a second opinion", "check this for bugs", "any issues with this code".
---

# /review — adversarial review

## When to use

Auto-fires on production tier (managed by roborev's post-commit hook). Manually invokable for ad-hoc reviews via the trigger phrases above.

## Procedure

1. **Detect engine availability** in this priority order:

   a. **roborev** — check if installed (`which roborev` or `roborev --version`) AND `[review] use_roborev = true` in `framework.config.toml`. If both, use it: `roborev review` for current diff. Roborev manages its own model selection, prompt, and output.

   b. **Claude Code built-in `/review`** — if running inside Claude Code and roborev unavailable, defer to the built-in review skill. It's already shipped and battle-tested for this exact use case.

   c. **Fallback: direct agent invocation** — if neither above, invoke `claude code -p "<reviewer-prompt>" --model <reviewer-model>` directly. The reviewer-prompt template is below.

2. **Apply cost gate.** Read `[review] min_diff_lines` from config (default 50). Skip review if diff is below threshold. Avoid theater on trivial changes.

3. **Use a different model from the writer.** Read `[review] writer` and `[review] reviewer` from config. If they're the same, surface a configuration warning.

4. **For the fallback path,** the reviewer prompt asks the model to:
   - Read the diff with a "find what's wrong" mindset
   - Surface findings in **roborev's four-tier severity scale**: `critical / high / medium / low`
   - `critical` = bugs that cause data loss, security holes, contract violations, money-safety failures
   - `high` = error handling gaps that bite under realistic load, missing validation on user-facing input, race conditions
   - `medium` = unclear naming, design smells, missing tests, brittle assumptions
   - `low` = style, formatting, minor inconsistencies (roborev's "nit" tier)
   - Output as `reviews/<commit-hash>.md` markdown for the fallback path (when roborev isn't installed). When roborev IS installed, reviews live in its SQLite DB at `~/.roborev/reviews.db` and are accessed via `roborev show <sha> --json` or `roborev tui`.

5. **Severity-graded action:**
   - `critical` or `high` findings present → pre-push hook refuses the push (queries roborev via `roborev show <sha> --json` and parses JSON; for fallback path, parses the markdown headers)
   - `medium` → logged, no blocking
   - `low` → logged only

## Output format

`reviews/<commit-hash>.md`:

```markdown
# Review: <hash>

**Reviewer:** <model>
**Diff:** <N> lines across <M> files
**Time:** <ISO timestamp>

## Critical
- `path/file:line` — <description>

## Important
- `path/file:line` — <description>

## Nits
- `path/file:line` — <description>
```

## Notes

- Engine priority: roborev > Claude Code built-in > Claude subprocess fallback
- The fallback exists so the framework keeps working when running outside Claude Code or when roborev is missing
- See `docs/spec.md` §12 for design rationale and the hedge

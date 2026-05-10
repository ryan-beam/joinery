---
name: workshop-session-start
description: |
  Read HANDOVER.md, run preflight checks, load context for a working session. Invoked by the `workshop session start` CLI command. Triggers when user says "starting a session", "let's pick up where I left off", "session start", "what's the state of things".
---

# /workshop-session-start — session-open ritual

## When to use

Fires at the start of a working session. Invoked automatically by `workshop session start` CLI subcommand. Manually invokable via the trigger phrases.

The output orients the user (or the agent's next-self) to where things were left.

## Procedure

1. **Read `HANDOVER.md`** and surface the four sections in plain language:
   - "Last session ended <when>. <What got done> ... <What's next>."
   - List open side quests
   - Note anything in "Notes for next-self"

2. **Run preflight checks** based on `framework.config.toml`:

   - **`git status`** — surface dirty tree if any uncommitted changes
   - **CI status** — if a PR exists for the current branch, check `gh pr checks` (when available); surface green/yellow/red
   - **Lints + types** — run `ruff check` and `mypy` (or biome and tsc for TS) without auto-fixing; surface counts of issues
   - **Tests** — run `pytest --collect-only` (or `vitest --reporter=verbose --no-color --bail=0` quickly) to verify the test suite is intact, NOT to actually run all tests
   - **Plan freshness** — read `plan.md` frontmatter. Production tier: warn if `Last updated` > 14 days old.

3. **Load active context:**
   - Top 3-5 open side quests from `learning/side-quests.md`
   - This week's primary/secondary ratio so far (read `learning/ratio-log.jsonl`)
   - Last 3 ADRs (most recent under `docs/decisions/`)

4. **Print the session-start summary** in a glanceable format:

   ```
   Last session ended <ISO> (<human-readable: "about 18 hours ago">).
   HANDOVER says: "<first line of What's next>"

   Preflight:
     git status:           clean | dirty (<N> files)
     CI on branch:         green | yellow | red | no PR
     Lints:                clean | <N> issues
     Types:                clean | <N> errors
     Tests:                <N> collected, suite intact
     plan.md freshness:    updated <N> days ago

   Active side quests: <K> open (oldest: SQ-NNN, <D> days)
   This week's ratio: <N>% primary / <M>% secondary (target: ≤70% secondary)

   Workshop is open. Ready when you are.
   ```

5. **If preflight surfaces a blocker** (e.g., dirty tree on a branch the user thought was clean, or a stale plan on production tier), do not start the session — flag it, ask the user how to handle.

## Output format

A glanceable terminal summary. Total lines: ~12-15. Should fit in one screen.

## Notes

- Token cost ~500 tokens for the session-start composition.
- Preflight commands themselves are deterministic shell — cost is in the agent's read of HANDOVER and the summary composition.
- The point is orientation, not interrogation. If the user just wants to start coding, they should be able to.
- Token cost ~500.

---
name: docs
description: |
  Survey the docs/ state, identify what needs updating, and compose the right sub-skills (docs-changelog, docs-getting-started, docs-architecture). The docs system orchestrator. Triggers when user says "update docs", "docs need updating", "refresh the documentation", "docs are stale".
---

# /docs — documentation system orchestrator

## When to use

Fires when the user wants to refresh the project's documentation surface. Composes the right sub-skills based on what's actually stale.

Triggers:
- "update docs" / "docs need updating"
- "refresh the documentation"
- "docs are stale"
- Auto-suggested by `/digest` when stale-detection fires

## Procedure

1. **Read `docs/` directory state.** For each tracked file:
   - `docs/architecture.md` — mtime, last commit that touched it
   - `docs/getting-started.md` — mtime, last commit
   - `docs/changelog.md` — mtime, last commit
   - `docs/decisions/` — count of ADRs, most recent
   - `docs/operations/*` (production tier) — mtime, last commit
   - `docs/reference/*` (production tier) — mtime, last commit

2. **Compare against codebase activity.** Use `git log --since=<file mtime>` to count commits that landed since each doc was last updated. Heuristic: a doc is stale if 5+ commits have shipped since its last update AND those commits touched related code.

3. **Surface what's stale to the user:**

   ```
   docs/architecture.md is stale: last updated 2026-04-15 (47 days ago).
   12 commits have shipped since, including 3 that changed top-level structure
   (src/auth/*, src/api/*).

   docs/getting-started.md is current.

   docs/changelog.md is missing entries for the last 8 commits (auto-update via /docs-changelog).
   ```

4. **Ask which to refresh.** The user picks one or more, OR says "all stale ones."

5. **Compose the sub-skills:**
   - Stale architecture → `/docs-architecture`
   - Stale getting-started → `/docs-getting-started`
   - Stale changelog → `/docs-changelog`

6. **Regenerate `docs/README.md` (the index)** automatically at the end. The index is mechanical — list all files in `docs/`, group by subdirectory, provide one-line descriptions. Always safe to regenerate.

7. **Commit refreshed docs** as separate commits per file (each is one logical change):

   ```
   docs: refresh architecture.md after auth restructure
   ```

   ```
   docs: regenerate index
   ```

## Output format

- Updated `docs/<file>.md` files for whatever was refreshed
- Always-updated `docs/README.md` (the index)
- One commit per refreshed doc

## Notes

- Stale-detection runs in `/digest` weekly. `/docs` orchestrator runs on demand.
- The index regeneration is mechanical and idempotent — safe to run at any time.
- Don't refresh docs that aren't actually stale. Empty PR diffs from "refresh everything" runs are theater.

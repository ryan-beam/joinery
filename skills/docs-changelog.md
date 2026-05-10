---
name: docs-changelog
description: |
  Update docs/changelog.md from recent commits and new ADRs since last update. Auto-runs Sundays as part of /digest. Manually invokable with "update changelog", "what changed", "generate changelog entries".
---

# /docs-changelog — update CHANGELOG from git

## When to use

Auto-fires Sundays as part of `/digest` (when `[docs] auto_changelog_in_digest = true`, the default). Manually invokable any time.

Triggers:
- "update changelog" / "regenerate changelog"
- "what changed since the last release"
- "generate changelog entries"
- Auto-runs in `/digest`

## Procedure

1. **Read existing `docs/changelog.md`** (or root `CHANGELOG.md` if that's the canonical location). Find the most recent dated entry to determine the range to backfill.

2. **Read git log** for commits since that date or version tag:
   ```
   git log --since="<last-entry-date>" --pretty=format:"%h %s"
   ```

3. **Filter for meaningful commits.** Per Keep a Changelog discipline:
   - Skip pure formatting/whitespace commits
   - Skip merge commits (the squash-merged content is what matters)
   - Skip dependency-bump commits unless they're security-relevant
   - KEEP: feat, fix, refactor (when user-visible), docs (substantive), perf, security

4. **Group commits into Keep a Changelog categories:**
   - **Added** — new features (feat)
   - **Changed** — changes to existing functionality (refactor, modified feat)
   - **Deprecated** — soon-to-be-removed features
   - **Removed** — removed features
   - **Fixed** — bug fixes (fix)
   - **Security** — security-relevant changes

5. **Read new ADRs** since last update. Cross-reference each ADR with the commits — note which decisions correspond to which changes.

6. **Compose the new entry** under `## [Unreleased]`:

   ```markdown
   ## [Unreleased]

   ### Added
   - <feature description> (<commit hash>)

   ### Changed
   - <change description> (<commit hash>; ADR-NNNN)

   ### Fixed
   - <fix description> (<commit hash>)
   ```

7. **Write back to `docs/changelog.md`** (or `CHANGELOG.md`). Keep entries concise — one line each.

8. **Commit:**

   ```
   docs: refresh changelog (<N> commits, <M> ADRs added)
   ```

## Output format

Updated `docs/changelog.md` (or `CHANGELOG.md`) with new entries under `## [Unreleased]`.

## Examples

**Before:**

```markdown
## [Unreleased]

### Added
- Initial signup form

## [0.1.0] — 2026-04-01
- First release
```

**After running /docs-changelog (covers 8 commits since 2026-04-01):**

```markdown
## [Unreleased]

### Added
- Initial signup form
- Form validation for email and password fields (a1b2c3; ADR-0007)
- /api/check-email endpoint for uniqueness check (b2c3d4)

### Changed
- Refactored UserMenu to use new auth context (c3d4e5)

### Fixed
- Logout button no longer persists session cookie (d4e5f6)

## [0.1.0] — 2026-04-01
- First release
```

## Notes

- Token cost ~1-2K
- Don't fabricate entries. If you can't tell what a commit did from its message, ask the user or skip it.
- The point is a navigable history, not exhaustive coverage. Quality over completeness.

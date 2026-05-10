---
name: pr
description: |
  Generate a PR description from plan.md and the current branch's diff. Output is Lore Protocol-flavored (context / considered / decided / ref) so the squash-merge commit on main becomes a clean, structured entry. Triggers when user says "open a PR", "send for review", "merge this branch", "draft the PR description", "I'm ready to PR this".
---

# /pr — generate a PR description

## When to use

Fires when the user is ready to open a PR for the current branch. Output is the PR body that GitHub (or other forge) will display.

Triggers:
- "open a PR" / "draft the PR" / "send for review"
- "merge this branch"
- "I'm ready to PR this"
- "write the PR description"

## Procedure

1. **Read the branch's diff against main.** `git diff main...HEAD` gives the cumulative changes on the branch.

2. **Read `plan.md`** to know what the work was supposed to accomplish.

3. **Read recent commits' messages** on this branch — they have intermediate context about decisions.

4. **Compose a Lore Protocol-flavored PR description:**

   ```markdown
   ## Summary

   <One-line summary of what this PR does.>

   ## Context

   <Why this change? What triggered it? What state does it leave things in? One paragraph.>

   ## Considered

   <Alternatives weighed during the work.>

   ## Rejected because

   <Why the alternatives lost.>

   ## Decided

   <The chosen approach, plainly stated.>

   ## Ref

   <Links: plan.md sections, ADR numbers, related issues, related PRs.>

   ---

   ## Checklist

   - [x] Branch name follows convention
   - [x] CI passes (ruff, mypy, tests)
   - [ ] Tests added or updated for behavior changes
   - [x] Documentation updated (if applicable)
   - [x] CHANGELOG.md updated under `## [Unreleased]`
   - [x] No emojis in code, configs, or commit messages
   - [x] No personal context in framework code or templates
   ```

5. **Pre-fill the checklist** based on what the diff actually contains. If the diff includes test files, mark "Tests added or updated" as `[x]`. If CHANGELOG.md was modified, mark that. Honesty matters — don't pre-check items that aren't true.

6. **Output options:**
   - Save to a temp file the user can copy into the GitHub PR creation form
   - Or output to stdout for paste
   - Or (future, when `gh` CLI is wired up) directly invoke `gh pr create --body-file <temp>`

## Output format

A markdown PR description following the Lore Protocol structure. Squash-merge will use this as the commit body on main.

## Examples

```markdown
## Summary

Add signup form validation for email and password fields.

## Context

Users could submit signup with empty or malformed inputs; the backend rejected but the UX was poor (server round-trip per attempt). plan.md §3 SC-1 through SC-4 specified client-side validation for the signup flow.

## Considered

- react-hook-form for validation
- Hand-rolled with useState + useEffect
- Server-side-only with optimistic UI

## Rejected because

- react-hook-form is overkill for one form (will revisit if we add 3+ more)
- Server-side-only had unacceptable UX cost (round-trip per check)

## Decided

Hand-rolled validation with useState + useDeferredValue for the async uniqueness check. Errors render via a separate ErrorMessage component for styling consistency.

## Ref

- plan.md §3 SC-1 through SC-4
- ADR-0007 (validation strategy decision)
- learning/side-quests.md SQ-042 (useDeferredValue)

---

## Checklist
[as above, pre-filled honestly]
```

## Notes

- Token cost ~1-2K
- The PR description IS the squash-merge commit body. Make it complete; don't expect the merge to add context.
- If the `gh` CLI is available, `/pr` can directly create the PR via `gh pr create`. If not, output to stdout for manual paste.

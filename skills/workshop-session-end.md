---
name: workshop-session-end
description: |
  Full session-close orchestrator. Verifies tests, detects branch state, presents merge/PR/keep/discard menu, then runs explain-back, handover, side-quest reconciliation, primary/secondary classification, and token report. The session-close ritual. Invoked by the `workshop session end` CLI command. Triggers when user says "ending the session", "wrapping up", "session end", "done for now", "close out this session", "finish this branch".
---

# /workshop-session-end — full session-close orchestrator

## When to use

Fires at end of a working session OR end of a feature branch. Invoked by `workshop session end` CLI subcommand (which does deterministic checks and hands off to this skill).

This is Phase 5 (Finishing) for the session-as-a-unit. Composes multiple sub-skills + makes the branch-finishing decision visible.

The orchestrator does seven things in order:
1. **Verify tests pass** (gate — don't continue if red)
2. **Detect branch state** (deterministic)
3. **Present the branch-finishing menu** (user decision)
4. **Execute the chosen path** (merge / PR / keep / discard)
5. **Comprehension gate** (`/explain-back`)
6. **Handoff** (`/handover` overwrites HANDOVER.md)
7. **Learning reconciliation + ratio + token report**

## Procedure

### Phase 1 — Verify tests pass

Before anything else, confirm the work is green.

1. Run the project's test suite. For Python: `pytest`. For TypeScript: `npm test` or equivalent. Read `framework.config.toml` for the configured test command if not standard.
2. Capture pass/fail counts + XFAIL counts.
3. If anything FAILED (not XFAIL — actually failed), stop the orchestrator and surface: *"Tests are red. The branch isn't ready to finish. Fix the failures first, then re-invoke."* Do NOT proceed to the menu.
4. If all passed (or only expected XFAIL): produce a `/verify` block with the test output as evidence, then proceed.

### Phase 2 — Detect branch state

Run these deterministic checks:

- Current branch name: `git branch --show-current`
- Main branch name: from `.workshop/config.toml` `[git.branching] main_branch`
- Commits ahead of main: `git rev-list --count origin/<main>..HEAD`
- Uncommitted changes: `git status --porcelain` (any output = dirty)
- Existing PR for this branch: `gh pr list --head <branch> --json number,state,url` (if `gh` is available)

Summarize the state to the user in a short block:

```
Branch state:
  Current branch:    feature/cut-state-machine
  Commits ahead:     4
  Uncommitted:       0 files
  Existing PR:       #18 (open) — https://github.com/owner/repo/pull/18
  Tier:              production
```

### Phase 3 — Present the menu

Based on branch state, surface a context-appropriate menu. The menu is the user's decision moment — don't bulldoze past it.

**Branch is `main`, no commits ahead:** "Nothing to finish on a branch. Skipping to comprehension gate (step 5)."

**Branch is `main`, commits ahead:** "You have unpushed commits on main. Choices:
  1. Push to origin/main
  2. Stop — this shouldn't be on main, want to move to a feature branch?"

**Branch is feature/*, no commits ahead of main:** "Feature branch with no diff. Choices:
  1. Delete the branch (nothing was done)
  2. Stay on it (more work coming)"

**Branch is feature/*, commits ahead of main, no existing PR:** "Feature branch with N commits, no PR yet. Choices:
  1. Open a PR (`gh pr create --fill`)
  2. Push the branch, defer PR
  3. Stay on it — more work coming this session"

**Branch is feature/*, commits ahead of main, existing PR:** "Feature branch with N commits, PR #X is open. Choices:
  1. Merge the PR (production tier: run `/review` first if not already)
  2. Push new commits + update PR
  3. Leave PR open, end session
  4. Stay on the branch — more work coming"

### Phase 4 — Execute the chosen path

**Production tier safety net before any merge:** if the user picks "merge" and `/review` hasn't run on the latest commit (no `reviews/<sha>.md` file exists), run `/review` automatically first. If `/review` produces Critical findings, refuse the merge and surface them. User can override only by explicitly running `/review` again or addressing the findings.

Execute the user's choice via the appropriate `gh` / `git` commands. Show the output. Confirm success before proceeding.

### Phase 5 — Comprehension gate (`/explain-back`)

Run `/explain-back` on the session's commits. Show the explain-back output to the user. Pause:

> "Read the explain-back. Anything surprising? Anything you'd phrase differently? Anything we should dig into before closing?"

Wait for the user's response. If they flag something surprising or unclear, that becomes a side quest (capture via `/sq <concept>`) before continuing.

### Phase 6 — Handoff (`/handover`)

Run `/handover` to overwrite `HANDOVER.md`. Show the new HANDOVER for the user to verify. If they want edits, take them now.

### Phase 7 — Learning reconciliation + ratio + token report

7a. **Side-quest reconciliation.** For each SQ opened or touched this session:
   - "Is this still open, or did the session close it?"
   - If closed: walk through `/sq close SQ-NNN` (the user writes the "What I now understand" field — never the agent).

7b. **Primary/secondary classification.** Two questions:
   - "Was this session primarily about learning a new thing, or shipping known stuff?"
   - "One-line note?"

   Append a JSONL line to `learning/ratio-log.jsonl`:
   ```jsonl
   {"date":"<YYYY-MM-DD>","type":"primary|secondary","project":"<name>","note":"<one-line>"}
   ```

7c. **Token report.** Read `.workshop/usage.jsonl` filtered to this session, aggregate by phase:

   ```
   Session token report:
     Drafting:   3,240 tokens
     Marking:    8,400 tokens
     Cutting:    47,820 tokens
     Finishing:  4,180 tokens
     Total:      63,640 tokens
     vs avg of last 5 sessions: -12%
   ```

7d. **Final commit (if anything in `learning/` changed):**

   ```
   session: <one-line summary of what got done>

   <optional Lore Protocol body if production tier and changes warrant>
   ```

## Final output

After all phases complete, print the session-end summary:

```
Session closed. <Brief recap from explain-back>.

Branch action: <merged PR #X | pushed feature/foo | kept on feature/bar | discarded>
Side quests:   <X> opened, <Y> closed this session.
Ratio entry:   primary | secondary — "<note>"
Tokens:        <total>, trend <+/-N>% vs avg.
Review status: <ran on commit <sha> | not required (no merge)>

HANDOVER updated. workshop session start picks up here.
```

## Output format

- Updated `HANDOVER.md`
- Possibly closed SQs in `learning/side-quests.md` + corresponding `learning/skills-log.md` entries
- New JSONL line in `learning/ratio-log.jsonl`
- One session-end commit if learning artifacts changed
- Possibly a merged PR / pushed branch (production-tier review gate enforced)
- Terminal summary

## Hard rules

- **Phase 1 (verify tests pass) is a gate, not a step.** Red tests = stop the orchestrator. Don't proceed to anything else.
- **Phase 3 (the menu) is the user's choice, never the agent's default.** Don't pick "merge" because it seems natural — present the options and wait.
- **Phase 4 production-tier review gate is non-negotiable.** No merge without a `/review` pass on the latest commit. Override requires explicit user action, never silent skip.
- **Phase 5 comprehension gate is human-only.** The agent's job ends at "here's the explain-back." The user decides if it's satisfactory.
- **Phase 7a SQ closures use the user's words, not the agent's.** Outsourcing synthesis to the agent defeats the comprehension purpose.

## Notes

- Token cost ~5-8K for the full ceremony (explain-back is the bulk).
- If `gh` is unavailable, skip the PR-state detection and have the user supply PR status manually.
- If `.workshop/usage.jsonl` is empty or missing, skip the token report quietly (don't fabricate numbers).
- Pairs with `workshop session start` on the next session — that skill reads HANDOVER.md and the SQ state this skill leaves behind.

## Pattern origin

Verify → detect-environment → menu → execute pattern adapted from obra/superpowers v5.1.0 `finishing-a-development-branch`. The Joinery version layers comprehension/handover/learning on top, which the upstream doesn't (upstream stops at branch-finishing; Joinery treats the session as the larger unit).

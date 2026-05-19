---
name: execute-plan
description: |
  Stop-condition-driven plan walker. Reads plan.md, finds the next unimplemented success criterion in §3, and works through it with explicit stop conditions between steps. The Cutting-phase discipline that prevents "just keep going" agent drift. Triggers when user says "execute the plan", "work through plan.md", "do the next cluster", "implement the next criterion", "let's cut".
---

# /execute-plan — stop-condition-driven plan walker

## When to use

Cutting phase. Only after Drafting and Marking are done.

Preconditions (verify before starting, refuse if missing):
- `plan.md` exists and is ratified (§3 Success Criteria filled in, §2 Files in Scope filled in)
- Failing tests exist for at least one criterion that hasn't been implemented yet
- The user has invoked this skill or one of its trigger phrases — don't auto-fire

Tier-aware (see §"Stop conditions per tier" below):
- **`production`** — confirm before AND after every criterion
- **`standard`** — confirm between criteria only
- **`sketch`** — no auto-stops; keep moving

If preconditions fail, surface what's missing and stop. Don't write code without a ratified plan and failing tests.

## The load-bearing principle: stop conditions are not optional

Agents drift. Given a green light and a long plan, an agent will:
- bleed scope into files outside §2
- silently "fix" something that wasn't broken
- chain three criteria together because the second one "obviously" needed the third
- skip a Forbidden Action because it seemed like a cleanup
- claim done when only the happy path passes

Stop conditions are how this skill refuses to do that. The agent surfaces state and waits for the user before crossing each boundary. The user is the brake. The plan is the contract. This skill is the enforcement.

"Just keep going" is the failure mode this skill exists to prevent. Don't optimize it away.

## Procedure

### Step 1 — Load the contract

Read `plan.md`. Extract:
- **§2 Files in Scope** — the only files Cutting may touch this cluster
- **§3 Success Criteria** — the ordered list of testable conditions
- **§4 Forbidden Actions** — what this cluster must NOT do (e.g. "do not touch the auth module," "do not add migrations")

If any of those sections are empty, stop. The plan isn't ratified.

### Step 2 — Find the next unimplemented criterion

Run the test suite. Map each currently-failing test to a §3 criterion. The next criterion to work is the first failing one in §3 order.

If no tests are failing, every criterion is implemented. Fall through to Finishing (`/explain-back`, `/handover`, `/review`).

If a failing test doesn't map to any §3 criterion, stop. Either the test is wrong or the plan is incomplete. Surface the mismatch — don't paper over it.

### Step 3 — STOP CONDITION (pre-implementation)

Surface this block to the user and wait:

```
About to implement criterion <N>: <one-line criterion>

  Failing tests:        <list of test IDs>
  Files in scope:       <list from plan.md §2>
  Forbidden actions:    <list from plan.md §4>
  Tier:                 <production|standard|sketch>

Confirm before proceeding.
```

Wait for explicit confirmation. On `production` tier this is mandatory. On `standard` tier this can be a short "ok" — but it still happens. On `sketch` skip this step.

If the user redirects (e.g. "actually do criterion 5 first"), re-run Step 2 with the new target.

### Step 4 — Implement the minimum to make the test pass

Constraints:
- Touch ONLY files listed in §2 Files in Scope
- Honor every item in §4 Forbidden Actions
- Write the minimum code that makes the failing test green — no speculative generalization, no "while I'm in here" cleanups
- If you discover the criterion can't be implemented without touching a file outside §2, STOP. Do not silently expand scope. Surface it: *"Criterion <N> requires touching `<file>` which is not in §2. Options: (a) add it to §2 and re-ratify, (b) defer this criterion, (c) reshape the criterion."* Wait.

If you discover a Forbidden Action is required, same drill — surface and wait.

### Step 5 — Verify

1. Run the test that maps to this criterion. If still red, debug. Use `/debug` if root cause isn't obvious within one or two attempts. Do not patch symptoms.
2. Once that test is green, run the full test suite. If anything previously-green is now red, you have a regression. Fix it before continuing — don't move on with red elsewhere.
3. Capture: which test went green, which files were touched, total tests pass/fail.

### Step 6 — STOP CONDITION (post-implementation)

Surface this block to the user and wait:

```
Criterion <N> complete.

  Files touched:   <list>
  Tests:           <X> previously-green still green, <Y> newly green, <Z> red
  Diff size:       <+N -M lines across K files>

Continue to next criterion, or stop here?
```

On `production` tier this is mandatory. On `standard` tier this can be brief. On `sketch` skip.

If the user wants to inspect the diff or run an ad-hoc check, wait. They get the brake.

### Step 7 — Loop or hand off

- If the user says continue → go to Step 2.
- If the user says stop, or all §3 criteria are now green → fall through to Finishing-phase suggestions: "Cluster complete. Next: `/explain-back` to verify comprehension, then `/review` (production tier) before merge, then `workshop session end` to close."

## Stop conditions per tier

Tier governs how strict the stops are. Read tier from `.workshop/config.toml`.

| Tier | Step 3 (pre) | Step 6 (post) | Scope-violation surface | Forbidden-action surface |
|---|---|---|---|---|
| `production` | **mandatory, explicit confirm** | **mandatory, explicit confirm** | always | always |
| `standard` | brief confirm (one line ok) | brief confirm between criteria, not every step | always | always |
| `sketch` | skip — continuous progress | skip — continuous progress | always (still) | always (still) |

Sketch tier still surfaces scope and forbidden-action violations. The stop conditions that get relaxed are the rhythm checks; the safety rails never relax.

## Interaction with other skills

- **`/mark`** — produces the failing tests this skill walks. If §3 has criteria with no failing tests yet, Marking isn't done. Send the user back to `/mark`.
- **`/debug`** — invoke when a test stays red after one or two implementation attempts. Don't keep guessing.
- **`/verify`** — the production-tier evidence rule applies. When Step 6 reports "tests pass," that claim needs the actual command output as evidence.
- **`/explain-back`** — runs after the cluster is complete. Comprehension gate before `/review` and merge.
- **`/review`** — production tier: invoke after the cluster is green, before opening/merging the PR. Can also run per-criterion on production tier if the user wants tighter feedback loops; default is per-cluster.
- **`workshop session end`** — the orchestrator that wraps Finishing. `/execute-plan` doesn't replace it; it hands off to it.

## Output format

This skill produces no new files. It updates:
- Source code in files listed in `plan.md` §2
- Test outcomes (failing tests turn green; ideally no other test moves)
- Terminal stop-condition blocks at Steps 3 and 6

Optional progress log: if `learning/cutting-log.jsonl` exists, append one line per completed criterion:

```jsonl
{"date":"<YYYY-MM-DD>","plan":"<plan.md path>","criterion":"<N>","files":["..."],"tests_green":<X>,"tier":"<tier>"}
```

Don't create the file if it doesn't exist — only append.

## Hard rules

1. **Production tier MUST stop between criteria.** No chaining. No "let me also knock out the next one." The post-implementation stop is the brake.
2. **Never silently expand §2 Files in Scope.** Discovering a needed file outside scope is a STOP, not a green light. Re-ratify the plan or defer the criterion.
3. **Never silently skip a §4 Forbidden Action.** If it has to happen, surface it. The Forbidden list is a contract, not a suggestion.
4. **Never claim a criterion done while any test is red.** Including pre-existing reds you didn't cause — surface them, don't ignore them.
5. **Never write code without a failing test mapped to a §3 criterion.** If no test is failing for it, Marking isn't done. Go back.
6. **Never run `/review` or merge from inside this skill.** This skill is Cutting only. Hand off to Finishing.

## Notes

- Token cost scales with criterion count. Each criterion is roughly: read plan + run tests + implement + run tests + two stop blocks. Budget ~3-8K per criterion depending on cluster size.
- If `plan.md` lists more criteria than the user wants to work in one session, that's fine — finish a subset, stop, hand off to `workshop session end`. Don't push for completion.
- Resumability: this skill is stateless between invocations. Step 2 (find next unimplemented criterion) is the resumption point. Walking the same plan in a later session just re-runs Step 1 → Step 2.

## Pattern origin

Stop-condition-driven plan walker adapted from obra/superpowers v5.1.0 `executing-plans` skill. The Joinery version tightens scope to plan.md §2/§3/§4 specifically, layers tier-gated stop strictness, and refuses to fan out to subagents — that's `/swarm`'s job, not this skill's.

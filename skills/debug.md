---
name: debug
description: |
  Systematic debugging via root-cause analysis. Four phases: reproduce → isolate → understand → fix. The discipline is "no fix without identified root cause." Adapted from obra/superpowers `systematic-debugging`. Triggers when user says "debug this", "this is broken", "why isn't this working", "I can't figure out why X happens", "help me debug", "find the bug".
---

# /debug — root-cause debugging discipline

## When to use

Fires when something doesn't work and the cause isn't obvious. Production tier: mandatory before any "fix" is attempted on a real bug. Other tiers: recommended.

The discipline this skill enforces: **no fix without identified root cause.** "I think this might work" is not a root cause. "The state changed because X path ran twice" is.

## Procedure

Four phases, in order. Don't skip phases.

### Phase 1 — Reproduce

You can't debug what you can't reproduce. Before anything else:

1. **State the symptom precisely.** Not "it's broken" — "function X returns N when called with Y, expected M". If you can't state it that precisely, you don't understand the problem yet; go gather more info.
2. **Reproduce it deterministically.** Smallest input that triggers the bug. If it only fires sometimes, the first job is finding the trigger — usually state, timing, or order.
3. **Capture the reproduction.** Test case, command, log excerpt — whatever makes the bug reliably reappear. If you can't reproduce, you can't verify the fix later.

**Stop condition:** If you cannot reproduce the bug in 30 minutes of focused effort, surface that. Either the bug is non-deterministic (different problem class) or you don't have the right observability. Don't bluff through.

### Phase 2 — Isolate

Narrow the bug to the smallest possible surface.

1. **Bisect.** Which commit introduced it? Which file? Which function? Which input value?
2. **Remove suspected causes one at a time.** Comment out, mock, replace with a stub. Watch the symptom flip.
3. **Trust the minimum reproduction.** When you have a 5-line repro, the bug lives in those 5 lines or what they call.

**Stop condition:** You can point at a specific line/branch and say "the bug lives here." Until then, keep isolating.

### Phase 3 — Understand

This is the load-bearing phase. The temptation is to skip from "I see what's wrong" to "let me fix it." Don't.

1. **State the root cause.** A one-sentence claim like: *"When request A arrives while B is still being processed, A reads B's partially-mutated state because mutex M is released before commit C completes."*
2. **Predict what fixing the root cause should change.** If your hypothesis is right, what test would now pass that was failing? What side effect should disappear?
3. **Verify the hypothesis BEFORE writing the fix.** Add logging, add a probe, run a thought experiment. If your prediction is wrong, your hypothesis is wrong.

**Stop condition:** You can write a one-sentence root cause that survives the "but why" question three times. *"The mutex is released early."* — but why? *"Because exception E unwinds the stack past the release call."* — but why? *"Because the try-block is wider than the lock's intended scope."* — that's a root cause.

### Phase 4 — Fix

Only now is fixing safe.

1. **Write the failing test first.** The bug should produce a test failure. Make that test exist. (In `production` tier, this is mandatory per the TDD rule.)
2. **Fix the root cause, not the symptom.** Adding a null check that hides a bad state propagation is treating the symptom; fixing what produces the bad state is the root cause.
3. **Verify the predicted change happens.** The Phase 3 prediction should hold — the failing test passes, the side effect disappears, no new failures.
4. **Look for siblings.** A root cause often has multiple symptoms. After fixing, grep for other call sites with the same shape — they probably have the same bug.

## Output format

A short report at the bottom of the debugging session (paste into the PR description or `dev/idea-fragments.md`):

```markdown
## Debug session: <bug summary>

**Symptom:** <precise statement>
**Reproduction:** <minimal repro>
**Root cause:** <one sentence, survived three "but why"s>
**Fix:** <what changed and why>
**Siblings checked:** <other call sites grepped, none / N found>
**Test added:** <path to failing-then-passing test>
```

## Notes

- **Don't accept "it works now" as a fix.** If you don't know why it works now, you don't know it won't break again. Keep going until you do.
- **The 30-minute reproduction limit is real.** If you can't reproduce, the bug isn't ready to be debugged — it's ready to be instrumented. Add observability first, then come back.
- **Logging is debugging.** When stuck, add 5x more logging than feels reasonable. Most bugs hide in unobservable code paths.
- **Pair with `/verify`** at the end. The fix isn't done until evidence-of-fix has been produced.

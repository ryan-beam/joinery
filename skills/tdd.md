---
name: tdd
description: |
  Strict RED-GREEN-REFACTOR cycle, tier-gated. Mandatory on production (no code without a test that was first observed to fail). Recommended on standard. Off on sketch. Pairs with /verify (evidence the test was red before going green). Different from /mark which is batch plan-to-tests; /tdd is the one-test-at-a-time loop. Triggers when user says "let's TDD this", "write the test first", "RED-GREEN-REFACTOR", "test-driven", "tdd loop".
---

# /tdd — strict RED-GREEN-REFACTOR loop, tier-gated

## When to use

Inside the Cutting phase, when you're about to write production code for a single small behavior change. Three concrete entry points:

- **Inside a `/swarm` cluster** — each writer subagent should follow this loop internally on production tier
- **Inside an `/execute-plan` criterion** — the per-criterion test that came from `/mark` is your RED; the implementation step is GREEN; the cleanup is REFACTOR
- **Standalone** — adding tests to existing code, fixing a bug, or making a change without the full Joinery 5-phase rhythm

`/mark` is batch translation (plan.md §3 → failing tests, all at once). `/tdd` is the per-test loop (one failing test → minimum code → green → repeat). You can use `/tdd` without `/mark`. On production tier you cannot use `/mark` without `/tdd` following it.

## The load-bearing principle: every line of production code starts as a failing test

A test written AFTER the code isn't a test of behavior. It's a test of what the code happens to do. The two look identical in the diff; they are completely different epistemically.

When the test comes first and is observed to fail, you have evidence that:
1. The test actually exercises the code path you think it does
2. Your change is what made it pass
3. The test would catch a regression if the behavior were broken later

When the test comes second, you have none of that. The test passes because the code already does the thing. It may pass for the wrong reason. It may not exercise the path at all. You'll never know — there's no signal.

RED-FIRST is not a ritual. It's how you get the signal.

## The three-step cycle

### RED — write ONE failing test, run it, observe the failure

Pick the next smallest behavior. Write one test for it. Just one. Resist the urge to write a whole test class.

Run the test. It must fail. The failure must be for the reason you expect — "function not implemented" or "assertion mismatch on the value we're about to add," NOT "import error" or "syntax error in the test file." A test that fails for the wrong reason is not yet RED.

**STOP CONDITION** — paste the failure output before writing any production code:

```
FAILED tests/test_foo.py::test_bar — AssertionError: expected 42, got 0
```

Do not proceed to GREEN until you have evidence on screen that the test is red for the right reason.

### GREEN — write the MINIMUM production code to pass that one test

Implement the smallest possible change. Hard-code the return value if that's literally what the test asks for. Resist the urge to implement the next test's behavior preemptively — that next behavior has no test yet, which means by definition you don't know its shape.

Run the test. It must pass. If other tests broke, you went too far — narrow the change.

**STOP CONDITION** — paste the pass output:

```
PASSED tests/test_foo.py::test_bar
```

Both the new test AND the full suite must be green before continuing.

### REFACTOR — clean up, with the safety net of green tests

With production code AND tests both green, look for:
- Duplication (between the new code and existing code)
- Naming that no longer matches what the code does
- Structural opportunities — extract function, collapse a conditional, rename a variable

Run the full suite after each refactor step. Tests must stay green. If a refactor turns the suite red, revert — that refactor wasn't safe.

**STOP CONDITION** — show what changed and confirm the suite is still green:

```
Refactored: extracted compute_offset() from inline expression at handler.py:47
Tests still green: PASSED 12, XFAIL 1
```

Then return to RED for the next behavior. The loop is the unit; one rotation is not "done."

## Tier-gated behavior

| Tier | /tdd mandatory? | Blocks commits? | Auto-invokes? |
|---|---|---|---|
| `production` | **Yes** | **Yes** — pre-commit + /review spot-check no untested production code | Auto-invokes when the agent is about to write production code in Cutting |
| `standard` | Recommended | No | Surfaces the workflow when user starts implementing; user can decline per-change |
| `sketch` | Off by default | No | Manual invoke only — user must say "let's TDD this" or similar |

Sketch tier exists for comprehension-first exploration. TDD ceremony fights iteration speed when you're still figuring out what the code SHOULD do. Don't force it where it doesn't belong. If a sketch-tier file matures into something production-shaped, promote the tier and apply `/tdd` discipline going forward.

## The hard rule (production tier)

**No production code lands in a commit on production tier without one of:**

1. A corresponding test that the same diff also adds, OR
2. Inline documentation linking to an already-merged test (with commit hash) that failed first against the new behavior

The pre-commit hook can spot the obvious violations (production file changed, no test file changed in same commit). `/review` should flag the subtler ones (test exists but was clearly written after — telltale: identical structure to the implementation, no edge cases, asserts on internal state instead of behavior).

**Don't lie about the order.** If asked for RED-first evidence, paste the actual failure output captured at RED time. Per `/verify` discipline, evidence precedes claims. "I wrote the test first, trust me" is not evidence.

## Interaction with other skills

- **`/mark`** — batch translation of plan.md §3 success criteria into failing tests. After `/mark` runs, you have N RED tests. `/tdd` is then run once per test: implement minimum code for test 1, refactor, move to test 2. /mark fills the RED slot in bulk; /tdd runs the GREEN-REFACTOR-RED rotation for each one.
- **`/verify`** — pairs on the RED step. `/verify` provides the evidence-must-precede-claims discipline; `/tdd` consumes it. The captured failure output IS the verify evidence for "this test was red first."
- **`/review`** — on production tier, `/review` SHOULD flag any production code added without a paired test addition in the same diff. This is the backstop when the pre-commit hook misses subtleties (e.g., test exists but was clearly written after).
- **`/swarm`** — each cluster's writer subagent should follow `/tdd` internally on production tier. The cluster's two-stage review then verifies the RED-first discipline held.

## Common violations + how /tdd catches them

- **"Wrote the code, then wrote the test."** Fails the RED gate — no failure output was captured, because at the moment of writing the test the code already made it pass. `/verify` evidence is missing.
- **"Wrote the test to match the code I already wrote."** The test isn't verifying behavior; it's a mirror of the implementation. Tells: asserts on internal state instead of contract, identical edge-case shape as the impl, no negative cases. `/review` catches these.
- **"Marked test as XFAIL because it's hard."** XFAIL is for documented expected-failures (platform-specific bugs, upstream issues, behaviors blocked behind a flag). It is not "I gave up." Punted work goes to `learning/side-quests.md` or `dev/idea-fragments.md`, not into XFAIL.
- **"Wrote the test, it passed first try because the code was already there."** That test didn't drive any change — it's not yet a useful test of THIS work. Either you're testing existing behavior (fine, but label it that way and don't claim it as TDD for the new change), or the new behavior wasn't actually new. Resolve before continuing.

## Escape hatches

- **Pure refactors with no behavior change** — tests for the existing behavior should already exist. If they don't, ADD them BEFORE refactoring. A refactor without test coverage is a behavior change you can't see.
- **Spike / exploration code** — drop the tier to `sketch`, do the spike, learn what shape the code wants. When you're ready to land it for real, promote the tier and rebuild with full `/tdd` discipline. The spike is throwaway; the production version is RED-first.
- **Bug fixes** — the failing test that demonstrates the bug IS the RED step. This is the most natural `/tdd` fit there is. Write the test that reproduces the bug, watch it fail, fix the bug, watch it pass. The fix lands with its regression test in the same commit.

## Hard rules

- **Production tier: no untested production code.** Period. RED-GREEN-REFACTOR in order, not just "all three steps existed eventually." Order is the rule.
- **Production tier: paste the RED failure output as evidence.** Per `/verify` — claims without evidence are not acceptable.
- **Standard tier: recommended, declinable per-change.** Surface the workflow; let the user opt out for a specific change. Don't be silent about the choice.
- **Sketch tier: off by default.** Don't volunteer `/tdd` ceremony when the user is exploring. Manual invoke only.
- **Never write production code in the same edit as the test it's supposed to fail against.** Two edits minimum: test goes in, you observe it fail, THEN implementation goes in. Same-edit submission means there is no RED observation.

## Pattern origin

Adapted from obra/superpowers v5.1.0 `test-driven-development` skill, which makes TDD universal across all work. Joinery's divergence is explicit and load-bearing: TDD is **tier-gated, not universal**. The `sketch` tier exists precisely for comprehension-first exploration where TDD ceremony fights the work — you're still figuring out what the code should DO, and writing tests first against an unknown contract produces noise, not signal. Production tier is where the iron law applies; sketch tier is where it gets out of the way. Documented divergence per `docs/audits/obra-superpowers-2026-05-18.md` §5.

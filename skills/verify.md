---
name: verify
description: |
  Evidence-before-claims gate. Forces production of concrete evidence (test output, command run, screenshot, log excerpt) before declaring work "done" or "working." Adapted from obra/superpowers `verification-before-completion`. Triggers when user says "verify this", "is it done?", "check that it works", "show me it works", "prove it", "before we ship".
---

# /verify — evidence-before-claims gate

## When to use

Fires at the end of any meaningful piece of work, before "done" is claimed. Production tier: mandatory before merge. Other tiers: recommended.

The discipline: **a claim is not evidence.** "It should work now" is not "it works now." Until you've produced something the user can read — a passing test, a curl response, a screenshot of the rendered page, a log line — the work isn't done.

## Procedure

1. **State what was supposed to happen.** Plain English. Match it back to the plan or the original ask. Be specific: "Function X returns N for input Y" not "the feature works."

2. **State what evidence would prove it.** Before running anything. Pick the smallest evidence that closes the claim:
   - Test output (preferred — the assertion was already written)
   - Command run + its output (`curl`, `lpr`, `pytest`, `git status`, etc.)
   - Log excerpt with the relevant line highlighted
   - Screenshot (if UI / external service involved)
   - DB query result (for state-change claims)

3. **Produce the evidence.** Actually run the thing. Capture the output. If the evidence doesn't show what you predicted, the work isn't done — go back to fixing, don't shrink the prediction.

4. **Show the evidence in the report.** Paste the output into the PR description, the session transcript, or wherever the claim is being made. **Without the evidence visible, the claim is unverified.**

## Output format

A short block at the end of the work:

```markdown
## Verification

**Claim:** <what was supposed to happen, one sentence>
**Evidence type:** <test output | command + output | log | screenshot | DB query>
**Evidence:**

```
<paste the actual output here>
```

**Verdict:** <verified | partial | failed>
```

## Hard rules

- **No "should work" language in the verdict.** Either verified or not.
- **Don't summarize evidence — paste it.** A summary loses the audit trail. Pasting takes 2 seconds.
- **Failing verification is a finding, not a failure of the verify step.** If verification reveals the work isn't done, that's the verify skill working correctly. Go fix the work, then re-verify.
- **Verification of work you did NOT do** still produces evidence (e.g., an agent claims a fix; you run the test and paste output). Don't take the claim at its word.

## Examples

**Bad:**
```
The idempotency stack is implemented and working.
```

**Good:**
```markdown
## Verification

**Claim:** A second batch run against a shipment with status='buying' and matching Shippo idempotency_key reuses the existing transaction without creating a new charge.

**Evidence type:** test output

**Evidence:**
```
$ pytest tests/test_idempotency.py::test_no_duplicate_buys_under_network_failure -v
============================= test session starts ==============================
tests/test_idempotency.py::test_no_duplicate_buys_under_network_failure PASSED
============================== 1 passed in 0.3s ==============================
```

**Verdict:** verified
```

## Pair with `/debug` and `/explain-back`

- After `/debug` produces a fix, `/verify` is the next step: prove the fix holds.
- Before `/explain-back` writes the session summary, `/verify` should have already produced the evidence the summary references. No claim in `/explain-back` should lack a `/verify` trace upstream.

## Notes

- Token cost is low — usually one command run + paste.
- The discipline this skill protects against is the most common AI-era failure mode: declaring work done because the last response sounded coherent, not because the work was confirmed.
- For shell commands, capture both stdout and stderr. The relevant evidence often hides in stderr.

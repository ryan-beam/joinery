---
name: receiving-review
description: |
  Verify-before-acting on review feedback. Triage findings by severity, distinguish "I disagree" from "you're wrong" from "fair point — fix it", and never silently dismiss without recording the reason. The discipline that keeps the writer-≠-reviewer principle honest from the writer's side. Triggers when user says "received review", "review feedback", "respond to review", "address the review", "I disagree with this review".
---

# /receiving-review — verify-before-acting on review feedback

## When to use

A roborev / `/review` / human reviewer has surfaced findings on the current branch or PR. Fire this skill before responding, before dismissing, before fixing.

The counterpart to `/review`: that skill produces findings; this skill is the discipline for handling them honestly.

## The load-bearing principle: the writer is the LEAST objective person to evaluate review feedback

The whole point of writer ≠ reviewer is that the writer is biased. So when the writer evaluates a finding, the default should be **"the reviewer probably saw something I missed"** — not "the reviewer doesn't understand my reasoning."

That bias asymmetry is what makes review work. Receiving-review is the skill of staying on the correct side of it.

## Triage by severity

Findings come tagged with roborev's four-tier scale (or the markdown headers from the `/review` fallback). Handle each tier differently:

- **critical** — Address immediately. No exceptions. If you're confident it's a false positive, get a SECOND independent review before dismissing. One bias-prone evaluator is not enough to overrule a critical finding.
- **high** — Address before merging unless you have a specific reason. Record the reason wherever the finding lives.
- **medium** — Address if cheap. Explicitly defer if expensive — capture as a side quest via `/sq <concept>` so it doesn't vanish.
- **low** — Style/nits. Batch-address or skip per team/project convention. Don't argue them individually.

## The three response categories

Every finding ends in one of these three. There is no fourth (no "ignore silently").

### "You're right — fix it"

The reviewer is correct. Apply the fix. Make a commit. Mark resolved in roborev (`roborev resolve <id>`).

For `/review` fallback path: edit `reviews/<sha>.md` to strike through the resolved finding with a "→ fixed in <commit>" note.

### "Fair point — record + defer"

The reviewer is right but this isn't the moment to fix it. Capture as a side quest via `/sq <concept>`. Mark the finding as dismissed-with-followup in roborev (`roborev defer <id> --sq <SQ-NNN>`).

The defer-with-SQ chain is what keeps "I'll get to it later" from being a lie.

### "I disagree — reason is X"

The most dangerous category. Requires writing down the disagreement in a way another reviewer could evaluate.

- **roborev:** `roborev dismiss <id> --reason "..."` with the actual reasoning, not "false positive" or "won't fix."
- **`/review` fallback:** write to `reviews/<sha>.md` under a `## Disagreements` section, one entry per dismissed finding with the reasoning.

If you can't articulate the disagreement in writing that another reviewer would find reasonable, you don't have a disagreement — you have a bias the reviewer caught.

## The verification step (before any of the three above)

Before deciding which category a finding falls into:

1. **Re-read the finding. Slowly.** First reads are pattern-matched; you skim what you expect.
2. **Re-read the diff at the location the finding points to.** Don't trust your memory of what's there.
3. **Read what the reviewer is ACTUALLY saying** — not the reframe in your head. The reframe is biased; the original isn't.
4. **Restate the finding in one sentence in the reviewer's words.** If you can't, you don't understand it yet. Don't respond.

This step is the gate. Skipping it is how findings get dismissed for reasons that don't survive scrutiny.

## The disagreement discipline

The dangerous category gets its own rules because it's where the writer's bias does the most damage.

- **"I disagree" is fine. "I disagree silently" is not.** Silent dismissal removes the finding from the audit trail. Production bugs live in the silent-dismissal pile.
- **Record the disagreement WITH REASON in the same place the finding lives.** roborev DB or `reviews/<sha>.md` — same artifact, so future readers see both sides.
- **The reasoning should pass the "would another reviewer agree this is a valid disagreement?" test.** Not "agree with my conclusion" — agree that the disagreement is reasoned, not reflexive.
- **If you can't articulate why the reviewer is wrong, the reviewer is probably right.** This is the single most important sentence in this skill.

## Common failure modes

- **Dismissing critical findings without a second review.** This is how production bugs ship. The writer's confidence that something is a false positive is exactly the bias the review process exists to counter.
- **Re-interpreting the finding into something the writer thinks they can dismiss.** The reframe is biased. Stick to the reviewer's words.
- **Treating `/review` findings as advisory when production tier requires addressing them.** Critical and high findings block in production tier. The pre-push hook + workshop session end Phase 1 gate enforce this; don't try to route around them.
- **Bulk-dismissing without per-finding reasoning** ("these are all nits"). Sometimes the reviewer batched a real bug into the nits list. Read each one.
- **Closing the loop in your head without closing it in the artifact.** If roborev still shows the finding open, it's open — regardless of what you intend to do about it.

## Tier behavior

- **production** — Every critical/high finding must be EITHER fixed OR dismissed-with-second-review-and-recorded-reason before merge. The pre-push hook + workshop session end Phase 1 (PR #21) enforce this. No exceptions.
- **standard** — Same in spirit but less strict. Critical findings still block; high findings are surfaced but don't gate.
- **sketch** — Findings are advisory; no blocking. Receiving-review is still useful for self-discipline, but the enforcement is off.

The tier setting in `framework.config.toml` determines which of the above applies.

## Hard rules

- **Critical findings can't be silently dismissed.** Either fixed, or dismissed-with-second-review-and-recorded-reason.
- **Disagreements must be recorded with reasoning** in the same artifact the finding lives in.
- **The writer's default is "the reviewer caught something I missed,"** not "the reviewer doesn't understand."
- **If you can't articulate the disagreement in writing, the disagreement isn't real.** Fix the code, not the finding.
- **Bulk-dismissal is forbidden.** Each finding gets read.

## Pattern origin

Adapted from obra/superpowers `receiving-code-review`. Differences from upstream:

- **Disagreement discipline is elevated** — upstream treats disagreement as one option; Joinery treats it as the dangerous option and gives it explicit shape (recorded reasoning, second-reviewer test).
- **Tier-gated enforcement via the pre-push hook + session-end gate** — upstream has no enforcement layer; Joinery's production tier blocks the merge if critical/high findings aren't resolved.
- **Side-quest integration** — deferred findings hook into `/sq` so the defer-with-followup chain is auditable; upstream has no equivalent.

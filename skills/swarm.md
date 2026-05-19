---
name: swarm
description: |
  Subagent-driven development. For plans with independent clusters, dispatches each cluster to a fresh isolated subagent (via Task tool) + per-task auto-review by a SECOND isolated subagent. Two-stage isolation: writer ≠ reviewer, both ≠ orchestrator. Parent session tracks all subagents via TodoWrite. Triggers when user says "swarm the plan", "dispatch agents for these clusters", "run multiple clusters in parallel", "let's parallelize this".
---

# /swarm — subagent-driven development

## When to use

Multi-cluster Cutting phase. Plan.md §3 Success Criteria has been split into clusters AND those clusters are **explicitly marked independent** (no cross-cluster dependencies). Marking phase is complete for every cluster — failing tests exist on disk for each one.

Tier gate:

- **production** — allowed, full ceremony required
- **standard** — allowed, full ceremony required (reviews are surfaced, not blocking)
- **sketch** — refused. The ceremony fights sketch-tier iteration speed. Use `/execute-plan` instead.

If you have only 1-2 clusters, don't reach for `/swarm`. The subagent overhead doesn't pay for itself below 3 independent clusters. Use `/execute-plan` and walk them serially.

## The load-bearing principle: writer isolated, reviewer isolated, both isolated from orchestrator

`/swarm` is honest at scale because of three-way isolation:

1. **Writer subagent** sees only its cluster's slice of plan.md (§2 Files in Scope for that cluster, §3 Success Criteria for that cluster, §4 Forbidden Actions). It cannot see the other clusters' work-in-progress, other writers' reasoning, or the orchestrator's wider context. It implements from scratch.

2. **Reviewer subagent** sees only the writer's *diff* and the cluster's §3 criteria. It does NOT see the writer's reasoning, scratch work, or chain-of-thought. It reviews the artifact, not the author.

3. **Orchestrator** (the parent session) sees only the outputs: which clusters passed, which findings each review surfaced, which clusters failed and why. It does NOT see how each implementer reasoned or what the reviewer was internally chewing on.

This is non-negotiable. Collapsing any of these three roles into one context defeats the pattern — you get a writer reviewing their own work, or an orchestrator unconsciously priming the reviewer with implementer-context. The whole point is that the diff has to stand on its own to a stranger.

## Precondition check

Before dispatching anything, verify ALL of these. If any fails, **STOP** and surface what's missing. Do not dispatch a partial swarm.

1. `plan.md` exists at project root AND is ratified (no open `[OPEN]` or `[TBD]` markers in §3).
2. §3 Success Criteria is organized into clusters — not a flat checklist.
3. Each cluster is explicitly marked independent. Suggested convention: `[INDEP]` tag at the cluster heading, OR an explicit line `Dependencies: none` under each cluster heading. If any cluster lacks the marker, refuse — the user must affirm independence in writing.
4. Failing tests exist on disk for every cluster (Marking phase complete for each). Run the test suite — every cluster's tests should be RED in a way that maps to its §3 criteria.
5. Tier is `production` or `standard`. Sketch refused.
6. Working tree is clean (`git status --porcelain` returns empty). Swarm needs a known baseline.
7. The Task tool is available in this harness. If running outside Claude Code or in a harness without the Task tool, refuse and surface "swarm requires the Task tool; this harness does not provide it."

If any precondition fails, surface a single block listing what's missing and stop. Do not dispatch.

## Dispatch procedure

For each independent cluster, spawn a **writer subagent** via the Task tool (`subagent_type="general-purpose"`). One Task call per cluster. Where the harness supports parallel Task calls in a single message, dispatch all writers in parallel — that's the whole point.

Each writer's prompt must include, and ONLY include:

- The cluster's §3 Success Criteria (just this cluster's, never the full plan)
- The cluster's §2 Files in Scope
- The full §4 Forbidden Actions (these are project-wide, not cluster-scoped)
- The tier (production / standard)
- The paths to the failing tests this writer must make pass
- The explicit instruction:

  > "Make the failing tests at <paths> pass. Do not modify any file outside §2 Files in Scope. Do not violate §4 Forbidden Actions. When the tests pass (or you cannot make them pass), stop and report. Do not proceed to other clusters. Do not run /review yourself — the orchestrator handles that."

Do NOT include in the writer's prompt:

- Other clusters' criteria or files
- The orchestrator's plan for the wider session
- Other writers' progress
- Roborev/review configuration
- Anything from learning/, HANDOVER.md, or other session state

Track each writer in **TodoWrite** — one task per cluster, `status: "in_progress"` from dispatch until the writer returns.

**Wait for all writers to complete (or fail) before proceeding to review.** Do not start any reviewer subagent while writers are still running — context bleed risk.

## Two-stage review

For every cluster where the writer succeeded (tests green, no error report), spawn a **reviewer subagent** via the Task tool (`subagent_type="general-purpose"`). One reviewer per succeeded cluster.

Each reviewer's prompt must include, and ONLY include:

- The cluster's diff (the patch the writer produced — `git diff` of the writer's commit)
- The cluster's §3 Success Criteria
- The cluster's tier
- The reviewer prompt template from `skills/review.md` step 4 — adapted: deliberately stripped of any implementer context. The reviewer does not know what the writer was thinking, only what it changed.

Do NOT include in the reviewer's prompt:

- The writer's reasoning, chain-of-thought, or scratch work
- The writer's report on what it did or didn't do
- Other clusters' diffs or reviews
- Anything the orchestrator added beyond the diff + criteria + tier

The reviewer outputs findings in the four-tier severity scale (`critical / high / medium / low`) per `skills/review.md`.

Save each cluster's review to `reviews/cluster-<name>-<sha>.md` with the following header:

```markdown
# Review: cluster-<name>-<sha>

**Engine:** swarm-reviewer-subagent
**Cluster:** <cluster-name>
**Writer commit:** <sha>
**Reviewer model:** <whatever the Task tool ran>
**Tier:** <production | standard>
**Time:** <ISO timestamp>

## Critical
- `path/file:line` — <description>

## High
- `path/file:line` — <description>

## Medium
- `path/file:line` — <description>

## Low
- `path/file:line` — <description>
```

The `Engine: swarm-reviewer-subagent` header distinguishes these from `/review`'s outputs (which use `roborev`, `claude-code-builtin`, or `fallback-subprocess`). Same `reviews/` directory, different engines, different filenames.

## Integration

Once all writers and all reviewers have returned, aggregate the results in the orchestrator and surface to the user — once, in one block. Do not surface findings as they trickle in; the user wants the whole picture at once.

**For each cluster, report:**

- **Succeeded clusters** — show the diff summary (files touched, lines +/-), the test status (all green), and the review findings grouped by severity.
- **Failed clusters** — show the writer's error report. Surface the cluster's spec (§3 criteria + §2 files) so the user can intervene manually if needed.
- **Mixed results across clusters** — present cluster-by-cluster, don't average.

**STOP CONDITION.** After surfacing the aggregate, **stop and wait for the user**. Even if every writer succeeded AND every reviewer was clean, **never auto-merge, never auto-push, never proceed to `/pr` or `workshop session end`**. The orchestrator's job ends at "here are the results." The user decides what merges, what gets reworked, what gets discarded.

## TodoWrite tracking

The parent session tracks every cluster as a TodoWrite task. The flow per cluster:

```
[pending]      "swarm cluster: <name> — writer dispatched"
   ↓
[in_progress] "swarm cluster: <name> — writer running"
   ↓
[in_progress] "swarm cluster: <name> — writer done, reviewer running"
   ↓
[completed]   "swarm cluster: <name> — writer green, review <severity>"
   OR
[completed]   "swarm cluster: <name> — writer failed, surfaced for manual intervention"
```

Update the TodoWrite list on every state transition. This is the user's only real-time view into the swarm — keep it accurate.

## Failure modes + escape hatches

**One writer fails, others succeed.**
The other writers proceed to review and report normally. The failed cluster is surfaced in the aggregate with the writer's error report + the cluster's spec re-printed inline so the user can pick up manually. Do not retry the failed writer automatically — the failure is a signal.

**One reviewer finds `critical` or `high`.**
Don't block dispatch of other reviewers. Once all reviews are in, surface the finding in the aggregate prominently. Production tier: the eventual pre-push hook (PR #21 surfacing layer + `/review` gate) will refuse the push, so the user can't accidentally merge through. Standard tier: surfaced not blocking. Sketch: N/A (swarm refused at precondition).

**All writers succeed but reviews are mixed across clusters.**
User decides cluster-by-cluster which to keep, which to rework, which to discard. Don't bundle the decision.

**A writer modifies files outside §2.**
The writer violated the explicit instruction. Treat this as a writer failure for that cluster — surface the out-of-scope diff and the violation. Do NOT integrate the cluster. The user decides whether to revert, rework, or accept the scope expansion (which retroactively requires a plan.md amendment).

**A writer returns claiming success but tests are still red when the orchestrator re-runs them.**
Same as the previous case — treat as failure. The writer's self-report is not the source of truth. The orchestrator should re-run the cluster's tests after the writer returns. If green, the writer succeeded. If red, the writer failed regardless of what it reported.

**Task tool unavailable mid-swarm.**
If a Task call errors out, treat that cluster's writer (or reviewer) as failed for this swarm. Surface in the aggregate. Do not silently retry.

## Tier behavior

- **production** — Full two-stage isolation required. Every cluster gets a writer + a reviewer. Reviews go to `reviews/cluster-<name>-<sha>.md`. `critical` or `high` findings will block the eventual push via the pre-push hook. Never skip review. Never silent merge.

- **standard** — Full two-stage isolation required. Every cluster gets a writer + a reviewer. Reviews are saved but **not** blocking — surfaced for user judgment. User can choose to merge with findings outstanding.

- **sketch** — `/swarm` refuses to run. Surface:

  > "Sketch tier is comprehension-first exploration. Subagent ceremony fights iteration speed. Use `/execute-plan` to walk clusters serially with the orchestrator in the loop."

## Hard rules

1. **Writer ≠ reviewer ≠ orchestrator.** Three distinct contexts. Collapsing any two defeats the pattern.
2. **No cross-cluster context bleed.** Each writer sees only its own cluster's slice. Each reviewer sees only its own cluster's diff. The orchestrator sees outputs, not internals.
3. **Never auto-merge.** Even with all green writers and all clean reviews, the orchestrator stops at the aggregate. Merging is a separate explicit user action.
4. **Failed precondition = stop.** Do not dispatch a partial swarm. Surface what's missing and let the user fix it.
5. **Re-run the cluster's tests after the writer returns.** The writer's self-report is not authoritative. Green tests on disk are.
6. **Reviews land in `reviews/` with the `Engine: swarm-reviewer-subagent` header.** Filename `cluster-<name>-<sha>.md`. This distinguishes them from `/review` outputs and keeps the audit trail honest.

## Notes

- Requires the Task tool — only available inside Claude Code (or Claude Code-compatible harnesses). Surface "swarm requires the Task tool" and refuse if unavailable. No fallback path; the isolation is the point.
- Most valuable on 3+ independent clusters. For 1-2 clusters, the orchestration overhead exceeds the parallelism gain — use `/execute-plan` instead.
- Reviews from `/swarm` and reviews from `/review` coexist in the same `reviews/` directory but with different engine headers and filename conventions. A single commit can legitimately have both — a `/swarm` cluster review at `reviews/cluster-foo-<sha>.md` AND a `/review` whole-branch review at `reviews/<sha>.md`. They're complementary, not redundant.
- Token cost scales linearly with cluster count (one writer + one reviewer per cluster). Budget accordingly — a 6-cluster swarm at production tier is meaningfully expensive.
- The TodoWrite list is the only real-time signal the user gets during dispatch. Keep it current or the user is flying blind.

## Pattern origin

Subagent-driven development is ported from obra/superpowers' `subagent-driven-development` skill (audit row #6, "most valuable port"). The upstream pattern is **one-stage**: fresh subagent per task, with the parent reviewing the result. Joinery layers a **two-stage** isolation on top — the reviewer is ALSO a fresh subagent, with no implementer context.

The two-stage extension is Joinery-specific. It exists to close audit hole #1 fully (`/review` doesn't auto-fire on cluster PRs). The companion port — `/review` as isolated subagent (PR #6) — isolates the **reviewer** when invoked standalone. `/swarm` isolates the **writer** AND chains the isolated reviewer per-cluster. Together they ensure: at no point does the same context both write and review the same code.

See `docs/audits/obra-superpowers-2026-05-18.md` lines 37, 69, and 96 for the original audit reasoning.

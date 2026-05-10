# ADR-0001: Tiers are risk profiles, not project categories

**Status:** Accepted
**Date:** 2026-05-10
**Decider:** Ryan Beam

## Context

A coding framework's discipline (planning rigor, type strictness, test gates, review enforcement) needs to scale with what's at stake. Most frameworks let users pick discipline levels by project size — small project = low rigor, large project = high rigor. That gets the discipline wrong-sized in two opposite directions:

- A 50-line bash script controlling production payments is "small" by line count but high-risk by consequence. Low-rigor framing ships bugs that cost real money.
- A 5,000-line hackathon throwaway is "large" by line count but zero-risk by consequence. High-rigor framing turns play into a chore.

Size doesn't track risk. Consequence does.

## Decision

Joinery's tier system (`production` / `standard` / `sketch`) configures defaults based on **risk profile**, not project size or category. Tier is chosen at `workshop init` time and recorded in `.workshop/config.toml`.

- **Production tier:** real users, real money, real consequences. All gates required. Full discipline.
- **Standard tier:** personal serious projects, internal tools, things you'll come back to. Most gates advisory.
- **Sketch tier:** throwaways, learning experiments. Minimal ceremony. Learning module preserved.

The framework's per-feature toggles (`framework.config.toml`) let users override tier defaults individually. **Tiers are starting points, not cages.** Tier promotion (`workshop promote --to <tier>`) is supported and additive. Tier demotion is intentionally not supported — if you no longer need production rigor, you're probably ready to archive or delete the project.

## Considered alternatives

**Tier by project size (LOC).** Rejected because risk doesn't track size. A small script can be high-stakes; a large project can be a throwaway.

**Tier by language.** Rejected because risk doesn't track language. Python and TypeScript projects can be at any risk level; the framework already supports both as first-class.

**Tier by deployment target.** Closer to right (deployed projects often have higher stakes), but doesn't catch local scripts that touch production resources (database migrations, payment scripts, system administration). Rejected as the primary axis but informs production tier's typical use cases.

**One tier with all knobs configurable.** Considered as the maximally flexible alternative — no tiers, just per-feature config. Rejected because tier presets reduce decision overhead at init time and provide sensible defaults for the 90% case. Power users still have full per-feature override.

**More than three tiers.** Considered (e.g., adding "experimental" between sketch and standard, or "critical" above production). Rejected because every additional tier doubles config surface and forces more decision overhead. Three tiers cover the meaningful risk gradients without over-engineering.

## Consequences

- Users have to think about *risk* when initializing a project, not just size or scope. The interactive `workshop init` prompt explicitly explains this.
- Production tier is heavyweight by design — full plan-gate, tdd-gate, ADRs, structured commits, branch+PR required, adversarial review on. If the project doesn't need this, pick standard instead.
- Sketch tier preserves learning module + explain-back even though most other gates are off. This is non-negotiable: comprehension never gets a free pass, even on throwaways.
- Tier promotion is additive (sketch → standard adds files, never removes). Demotion isn't supported, so picking too high is somewhat sticky — leans against picking production for things that aren't truly production.
- The risk-based framing forces honest assessment. "Is this really production-tier work?" is a useful question to answer at project start.

## References

- Spec §4 (Three Tiers)
- Spec §1 (the non-negotiables that lead to this design)
- Spec §14 (Configuration Reference for tier defaults)

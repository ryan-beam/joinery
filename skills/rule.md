---
name: rule
description: |
  Capture a real failure as a new CLAUDE.md rule. Hashimoto's scars-not-theory pattern formalized. MANUAL ONLY — never auto-invoked. The user decides when a failure deserves a rule. 3-strikes rule for non-catastrophic patterns; immediate rule for catastrophic single failures (security, data loss). Triggers when user says "this should be a rule", "/rule X", "we need to encode this lesson", "this just bit me again".
---

# /rule — failure-driven CLAUDE.md rule

## When to use

**Manual only.** Auto-invocation would produce rule bloat. The user decides when a failure deserves a rule.

Triggers:
- "this should be a rule"
- "/rule X" (explicit invocation)
- "we need to encode this lesson"
- "this just bit me again — third time now"

The threshold:
- **Catastrophic single failure** (security, data loss, money): immediate rule
- **Non-catastrophic recurring pattern**: 3-strikes rule (same kind of mistake 3 times = rule-worthy)
- **Theoretical concerns**: never. Wait for a real failure.

## Procedure

1. **Walk the user through four questions:**

   - **What was the mistake?** (one paragraph; the actual failure, not the abstract pattern)
   - **What rule would have prevented it?** (one rule, specific not abstract — "don't auto-mock external APIs in tests" beats "be careful with mocks")
   - **Where does it belong?**
     - Project `CLAUDE.md` for project-specific scars
     - Workshop-level `~/.config/joinery/CLAUDE.md` for cross-project standards (rare; usually only after a pattern proves sticky across multiple projects)
   - **What does the rule replace or refine?** Don't add a 12th rule when an existing 11th can be refined. Surface the existing rules and ask if any should be merged or updated instead.

2. **Generate the rule entry** in the chosen location:

   - Project CLAUDE.md: append a new rule with a number incremented from existing rules
   - Workshop-level: append to the appropriate section (Code style / Process / Conventions) per `docs/spec.md` §11

3. **Open in editor for refinement.** The user reviews the wording. Sharp prose matters here — vague rules don't enforce.

4. **Commit with a message linking back to the failure:**

   ```
   rule: don't auto-mock external APIs in tests

   Added after my-project commit a1b2c3 silently passed unit tests but
   crashed in staging because the mock didn't match Stripe's actual response shape.
   Rule will block this class of failure on production tier.
   ```

5. **Commit references the failure hash** when one exists. If the failure was a near-miss (caught before commit), reference the conversation or PR.

## Output format

- Updated CLAUDE.md (project or workshop) with the new rule appended
- A commit landing the rule, with body linking to the failure

## Examples

**Project CLAUDE.md addition:**

```markdown
6. **Don't auto-mock external APIs in tests.** Use real-fixture mocks (recorded responses) or contract tests with the actual API. Mocks that don't match real responses pass unit tests but break in production. Added 2026-05-15 after the Stripe response-shape incident (commit a1b2c3).
```

**Commit message:**

```
rule: don't auto-mock external APIs in tests

Added after my-project commit a1b2c3 silently passed unit tests but
crashed in staging because the mock didn't match Stripe's actual response shape.
Rule will block this class of failure on production tier.
```

## Notes

- Token cost ~500. Cheap.
- The git log of CLAUDE.md becomes a chronicle of every lesson learned.
- Theoretical rules don't get added. There's no triggering failure. If you're tempted, ask yourself: what specific incident am I responding to?
- Workshop-level rules are rare. They only get added when a preference proves sticky across multiple projects. The discipline is "edit project CLAUDE.md from scars; edit workshop-level from standards."

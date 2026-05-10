---
name: security-review
description: |
  Run a security-focused review on the current branch or PR. Different prompting from /review (threat-model framing) and typically a deeper model (Opus by default). Wraps Claude Code's built-in /security-review when available; falls back to roborev with security flag, then to Claude subprocess with security prompt. MANUAL ONLY — no auto-invocation. Triggers when user says "security review", "audit for security", "check for vulnerabilities", "threat-model this".
---

# /security-review — security-focused adversarial review

## When to use

**Manual only.** Deliberately not auto-invoked. The user decides when a path warrants a security review.

Triggers:
- "security review" / "audit for security" / "audit this for vulns"
- "check for vulnerabilities"
- "threat-model this"
- "what could an attacker do here"

Production tier may also trigger this on PR creation when `[features] security_review = "pr-only"`.

## Procedure

1. **Detect engine availability** in this priority order:

   a. **Claude Code built-in `/security-review`** — if running inside Claude Code, defer to it. It's already shipped and battle-tested for security review specifically.

   b. **roborev with security flag** — if roborev installed, invoke with security mode (check roborev's docs for the exact flag).

   c. **Fallback: direct agent invocation** with a security-focused prompt and the deep_reviewer model (Opus by default).

2. **Use the deep_reviewer model.** Read `[review] deep_reviewer` from config. Security review warrants the most capable model since findings have outsized impact when missed.

3. **Threat-model framing.** The reviewer prompt should ask:
   - What can an attacker control? (Inputs, headers, environment, file paths, etc.)
   - What boundaries are crossed? (Trust zones, privilege levels, network)
   - What can go wrong on the boundaries? (Injection, traversal, escalation, leaks)
   - What's the blast radius if exploited? (Rows affected, data exposed, state corrupted)

4. **No cost gate by default.** Security review is deliberate and expensive. Don't skip on small diffs — a 5-line change can introduce a critical vuln.

5. **Severity treats Critical seriously.** Critical security findings ALWAYS block push (regardless of `[features] adversarial_review` setting). Important and Nits log only.

## Output format

`reviews/<commit-hash>.security.md`:

```markdown
# Security review: <hash>

**Reviewer:** <model>
**Diff:** <N> lines across <M> files
**Time:** <ISO timestamp>
**Threat model:** <one line summary of the trust boundaries crossed>

## Critical
- `path/file:line` — <vuln class>: <description>; <suggested fix>

## Important
- `path/file:line` — <description>; <suggested fix>

## Nits
- `path/file:line` — <description>
```

## Notes

- Engine priority: Claude Code built-in /security-review > roborev w/ security mode > Claude subprocess fallback
- Use deep_reviewer (Opus default), not the cheaper reviewer model
- Critical findings always block — security is non-negotiable
- See `docs/spec.md` §12 for design rationale

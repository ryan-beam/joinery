---
name: explain-back
description: |
  Agent summarizes what was built, decisions made, tradeoffs considered, and anything surprising. The first sub-step of Phase 5 (Finishing). Output is a transcript the user reads as the comprehension gate. Triggers when user says "walk me through what we built", "summarize what changed", "explain what just happened", "what did we just do", or auto-fires at session end via workshop session end.
---

# /explain-back — agent summarizes the work for the comprehension gate

## When to use

Fires at end of session, end of feature, or commit checkpoint. Auto-invoked by `workshop session end`. Manually invokable for ad-hoc comprehension checks.

The output is the comprehension gate's input. The user reads this and has to decide: do I understand everything here, or is something surprising?

## Procedure

1. **Identify the scope.** What changes are being explained back?
   - End of session: all commits since last `workshop session start`
   - End of feature: all commits on the current branch
   - Single commit: just the diff of that commit
   - Manual: ask the user what scope they want

2. **Read the diff and any related context.** Read `plan.md` to know what the work was supposed to accomplish.

3. **Structure the explanation:**

   **What changed:** plain-English description of the changes. Not a paraphrase of the diff — a description of intent and effect.

   **Decisions made:** non-trivial choices that came up during cutting. Why this approach over alternatives.

   **Tradeoffs considered:** what was weighed and rejected, with one-line rationale.

   **Anything surprising:** if the diff went in a direction the plan didn't anticipate, surface it. If a previously-unfamiliar concept came up, surface it (candidate side quest).

4. **Plain English over jargon.** The user is reading this to test their own understanding. Jargon hides gaps; plain language exposes them.

5. **Be honest about uncertainty.** If you used a pattern you're not fully sure of, say so: "I used `useDeferredValue` here — I'm reasonably confident this is right but it'd be worth double-checking the React docs." That triggers a side quest.

## Output format

A markdown transcript with four sections (What changed, Decisions made, Tradeoffs considered, Anything surprising). Suitable for pasting into HANDOVER.md or reading inline at session end.

## Examples

```markdown
## Explain-back: form validation feature

**What changed:**
Added client-side validation to the signup form. Email field now checks for valid format and uniqueness; password field checks for minimum length and complexity. Errors display inline below each field.

**Decisions made:**
- Validation runs on blur, not on every keystroke, to avoid noise. Debouncing for the uniqueness check (300ms) so we don't hammer the API.
- Errors render via a separate ErrorMessage component rather than inline JSX, so styling can change once without touching every form.

**Tradeoffs considered:**
- Considered react-hook-form for the validation, but the form is small enough that hand-rolled is simpler. Will revisit if we add 3+ more forms.
- Considered server-side-only validation, but the UX cost (round-trip per check) was too high.

**Anything surprising:**
- I used `useDeferredValue` on the uniqueness-check input. I'm fairly sure this is the right pattern for "snappy input, deferred async check" but it's not a pattern I've fully internalized. Worth a side quest.
```

## Notes

- Auto-triggers a side quest entry when the agent flags uncertainty about a concept.
- Token cost ~1-2K. Cheap.
- Comprehension gate that follows is human-only — the agent's job ends here.

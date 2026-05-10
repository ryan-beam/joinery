---
name: mark
description: |
  Translate plan.md success criteria into failing tests + type contracts. Phase 3 of the workflow (Marking). The pencil lines on the wood before the saw. Triggers when user says "write the tests", "mark this", "let's set up the tests for X", "translate the plan to tests", or auto-fires after /plan completes when the conversation indicates "let's start coding".
---

# /mark — failing tests from plan success criteria

## When to use

Fires after `plan.md` Section 3 (Success criteria) is populated. Translates each success criterion into a failing test. The handoff to Cutting becomes unambiguous: "make these failing tests pass, don't touch anything else."

Triggers:
- "write the tests" / "mark this" / "let's set up tests for X"
- "translate the plan to tests"
- Auto-fires after `/plan` completes when user signals readiness to code

## Procedure

1. **Read `plan.md` Section 3.** Each `- [ ]` checkbox is a success criterion. Each becomes one or more failing tests.

2. **Read project language detection.** Check `framework.config.toml [lang]` and detect from project files. Use the appropriate test runner:
   - Python: pytest, with `pytest.mark.xfail(strict=True)` for failing markers
   - TypeScript: vitest, with `test.todo` or `test.fails`

3. **For each success criterion, write a failing test:**
   - Test name describes the criterion in plain language
   - Test body asserts the criterion's expected behavior
   - Mark it as expected-to-fail (the framework runner will not error on these until cutting passes them)

4. **Type contracts where applicable.** If the plan implies new public types or interfaces, scaffold the type stubs:
   - Python: function signatures with `...` body and full type hints
   - TypeScript: interface/type declarations with no implementation

5. **Append a "marking notes" section to `plan.md`** if test design surfaced new questions:
   ```markdown
   ## Marking notes (appended {{date}})

   - SC-3 ("rejects empty input") was ambiguous: empty string vs missing field?
     Resolved: both treated as empty for this test, separate tests for each.
   ```

6. **Commit the failing tests** with a clear message:
   ```
   test: scaffold failing tests for plan §3 success criteria
   ```

## Output format

- One or more test files in `tests/` (or language-appropriate test directory)
- Optional type stubs in source directories
- Optional "Marking notes" section appended to `plan.md`
- A commit landing the failing tests

## Examples

**Python (pytest):**

```python
import pytest

@pytest.mark.xfail(strict=True, reason="not yet implemented")
def test_logout_button_calls_api_logout():
    # SC-1: clicking logout button calls /api/logout
    ...

@pytest.mark.xfail(strict=True, reason="not yet implemented")
def test_logout_button_redirects_to_login():
    # SC-2: after logout, user redirected to /login
    ...
```

**TypeScript (vitest):**

```typescript
import { test, expect } from "vitest";

test.fails("clicking logout button calls /api/logout", async () => {
  // SC-1
});

test.fails("after logout, user redirected to /login", async () => {
  // SC-2
});
```

## Notes

- Tier behavior: production = required before any cutting; standard = advisory; sketch = skipped.
- The handoff to /cut (Phase 4) is "make these failing tests pass, don't touch anything else."
- If a success criterion is ambiguous to test, that's a plan refinement signal, not a marking failure. Surface back to /plan.

# tests/

Pytest tests for the workshop CLI. Filled in **Phase 4** of the build.

## What lives here (after Phase 4)

```
tests/
├── __init__.py
├── test_init.py        # 9 paths: 3 tiers x 3 lang modes (python/typescript/polyglot)
├── test_session.py     # session start/end behavior
├── test_promote.py     # additive scaffold upgrade behavior
├── test_doctor.py      # config sanity checks
├── test_lang.py        # language detection from cwd contents
└── test_config.py      # config.toml render/read round-trip
```

## Phase 4 testing principles

- Tests assert behavior, not implementation. Refactoring `init.py` should not break tests if behavior is preserved.
- Use pytest fixtures for tmp directories, sample configs, mock subprocess calls.
- Test paths with spaces and Unicode characters (Windows compatibility).
- Coverage theater is forbidden — tests must fail when behavior breaks.

Run via `pytest` from the repo root.

See [`../docs/spec.md`](../docs/spec.md) §14 (Configuration Reference) for what gets tested. See [`../plan.md`](../plan.md) §3 for Phase 4 success criteria.

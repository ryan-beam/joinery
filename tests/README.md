# tests/

Pytest tests for the workshop CLI. 42 tests across 5 modules.

## Coverage

```
tests/
├── __init__.py
├── test_init.py            # 9 init paths: 3 tiers × 3 lang modes; plus path-with-spaces, refuse-existing-dir
├── test_lang.py            # Language detection from pyproject.toml, package.json, tsconfig.json, both, neither
├── test_config.py          # .workshop/config.toml read + tier/language helpers
├── test_templates.py       # Jinja2 rendering with placeholders; StrictUndefined error path
└── test_doctor_promote.py  # CliRunner integration tests for doctor + promote subcommands
```

## Discipline

- Tests assert behavior, not implementation. Refactoring an internal helper without changing public behavior shouldn't break tests.
- `tmp_path` fixtures for any filesystem work; no test pollutes the working tree.
- Paths with spaces tested (Windows compatibility).
- Coverage theater is forbidden — tests must fail when behavior breaks.

## Running

```bash
pytest                    # full suite
pytest -x                 # stop at first failure
pytest -k init            # only tests matching "init"
pytest --collect-only     # see what's collected without running
```

# src/joinery/

The Python source for the `workshop` CLI. Filled in **Phase 4** of the build.

## What lives here (after Phase 4)

```
src/joinery/
├── __init__.py         # package marker, version
├── cli.py              # click entry point with subcommand tree
├── init.py             # workshop init — scaffold new project
├── session.py          # workshop session start/end — wraps Phase 2 skills
├── promote.py          # workshop promote — additive scaffold upgrade
├── doctor.py           # workshop doctor — config sanity check
├── lang.py             # language detection
├── config.py           # framework.config.toml render/read
├── templates.py        # template copy + variable substitution
└── git.py              # subprocess wrappers for git init, commit, status
```

## Subcommands

- `workshop init <name>` — scaffold a new project (interactive or flag-driven)
- `workshop session start` — read HANDOVER, run preflight, load context
- `workshop session end` — explain-back + handover + sq reconcile + token report
- `workshop promote <name> --to <tier>` — additive scaffold upgrade
- `workshop doctor` — verify statusline + hooks + roborev + config
- `workshop --version`, `workshop --help`

## Phase 4 quality bar

The workshop CLI eats its own production-tier dogfood:
- mypy --strict on the codebase itself
- ruff format + ruff check pass
- Real tests (pytest) covering 9 init permutations + session/promote/doctor
- pathlib everywhere (no `os.path.join`, no path string concatenation)
- Jinja2 for template rendering (not naive `str.replace()`)
- Errors look like errors (one-line messages), not stack traces

See [`../../docs/spec.md`](../../docs/spec.md) §5 (Project Layout) and §14 (Configuration Reference). See [`../../plan.md`](../../plan.md) §3 for Phase 4 success criteria.

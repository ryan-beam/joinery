# src/joinery/

The Python source for the `workshop` CLI. Click-based command-line app with `init`, `session start/end`, `promote`, and `doctor` subcommands.

## Module layout

```
src/joinery/
├── __init__.py         # package marker, version
├── cli.py              # click entry point with subcommand tree
├── init.py             # workshop init — scaffold new project
├── session.py          # workshop session start/end framing
├── promote.py          # workshop promote — additive scaffold upgrade
├── doctor.py           # workshop doctor — config sanity check
├── lang.py             # language detection (python/typescript/polyglot)
├── config.py           # .workshop/config.toml read helpers (stdlib tomllib)
├── templates.py        # Jinja2 rendering with StrictUndefined
├── git.py              # subprocess wrappers for git init, add, commit, status
└── paths.py            # locate templates/, hooks/, skills/ for editable + wheel installs
```

## Subcommands

- `workshop init <name>` — scaffold a new project (interactive or flag-driven)
- `workshop session start` — read HANDOVER, run preflight, load context
- `workshop session end` — frame the session-end ritual (skills handle the agent-driven steps)
- `workshop promote <name> --to <tier>` — additive scaffold upgrade (sketch → standard → production)
- `workshop doctor` — verify workshop + project health
- `workshop --version` / `workshop --help`

## Quality bar

The workshop CLI eats its own production-tier dogfood:

- `mypy --strict` on the codebase (no `Any` returns, full type coverage)
- `ruff check` and `ruff format --check` clean (rule sets: E, W, F, I, B, C4, UP, S, N)
- 42 pytest tests covering 9 init permutations + session/promote/doctor + lang detection + config round-trip + template rendering
- `pathlib` everywhere; zero `os.path.join` or path string concatenation
- Subprocess only where genuinely needed (git operations)

## Dependencies

- `click>=8.1` — CLI framework
- `jinja2>=3.1` — template rendering with `StrictUndefined`
- Python 3.11+ (stdlib `tomllib`)

See `docs/spec.md` §5 (Workshop binary host) for design rationale.

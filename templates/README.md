# templates/

Static markdown and TOML files that `workshop init` copies into new projects, with Jinja2 `{{var}}` placeholders rendered against project-specific values.

## What lives here

```
templates/
├── CLAUDE.md.starter           # 5-rule project starter (becomes CLAUDE.md)
├── CLAUDE.md.global            # workshop-level defaults (~/.config/joinery/CLAUDE.md)
├── plan.md.template            # plan.md template per spec §6
├── HANDOVER.md.template        # session handoff format
├── README.md.template          # project README skeleton
├── AGENTS.md.template          # mirror of CLAUDE.md for Cursor/Codex
├── learning/
│   ├── side-quests.md.template
│   ├── skills-log.md.template
│   ├── comprehension-audits.md.template
│   ├── ratio-log.jsonl.template
│   └── weekly-digest.md.template
├── docs/
│   └── decisions/
│       └── 0001-tier-selection.md.template
└── config/
    ├── framework.config.toml.production    # tier defaults per spec §14
    ├── framework.config.toml.standard
    └── framework.config.toml.sketch
```

## Placeholder variables

Templates use Jinja2 `{{var}}` syntax. The `workshop init` command renders them against this context:

| Variable | Value |
|---|---|
| `{{project_name}}` | Project name from `workshop init <name>` |
| `{{tier}}` | `production` / `standard` / `sketch` |
| `{{language}}` | `python` / `typescript` / `polyglot` |
| `{{date}}` | ISO 8601 date at init time |
| `{{init_at}}` | Full ISO 8601 timestamp |
| `{{joinery_version}}` | Framework version |

## Adding a new template

1. Add the file here with appropriate placeholders
2. Update `src/joinery/init.py` to copy it
3. Add the variable to `render_context()` in `src/joinery/templates.py` if new placeholders are needed
4. Add a test in `tests/test_init.py` asserting the file is present after `scaffold()`

See [`../docs/spec.md`](../docs/spec.md) §5 (Project Layout) and §6 (plan.md Template) for the content specifications.

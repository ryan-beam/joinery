# templates/

Static markdown templates that `workshop init` copies into new projects. Filled in **Phase 1** of the build.

## What lives here (after Phase 1)

```
templates/
├── CLAUDE.md.starter           # the 5-rule starter (project-level)
├── CLAUDE.md.global            # workshop-level defaults (~/.config/joinery/)
├── plan.md.template            # the structured plan template
├── HANDOVER.md.template        # session handoff format
├── README.md.template          # project README skeleton
├── AGENTS.md.template          # mirror of CLAUDE.md
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
    ├── framework.config.toml.production
    ├── framework.config.toml.standard
    └── framework.config.toml.sketch
```

## Templating syntax

Placeholders use Jinja2-style `{{var}}` syntax. Common variables:

- `{{project_name}}` — the project name from `workshop init <name>`
- `{{tier}}` — production / standard / sketch
- `{{language}}` — python / typescript / polyglot
- `{{date}}` — ISO 8601 date at init time
- `{{init_at}}` — full ISO 8601 timestamp at init time

## Phase 1 quality bar

Each template ships ready-to-use. No "polish later" sections. Placeholders consistent across templates. The 5-rule starter feels right (you'd actually keep it on a real project).

See [`../docs/spec.md`](../docs/spec.md) §5 (Project Layout) and §6 (plan.md Template) for the full content specifications. See [`../plan.md`](../plan.md) §3 for Phase 1 success criteria.

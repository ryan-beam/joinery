# hooks/

The 4 git hook bash scripts that `workshop init` installs into `.git/hooks/` of scaffolded projects. Filled in **Phase 3** of the build.

Note: Joinery owns 4 hooks. The 5th (post-commit, for adversarial review) is managed by [roborev](https://github.com/roborev-dev/roborev), which Joinery adopts as its review engine.

## What lives here (after Phase 3)

```
hooks/
├── pre-commit          # lint + type-check + test + AGENTS.md mirror
├── pre-push            # last-line-of-defense; refuses direct main pushes on production
├── commit-msg          # Lore Protocol structure check; bot/daemon authors bypass
└── post-merge          # preflight refresh after pulling/merging
```

## Implementation principles

- **< 50 lines per hook.** Transparent on read. If you can't see what it does in 30 seconds, refactor.
- **`set -euo pipefail`** at the top of every script. No silent error swallowing.
- **Specific error messages.** Name the rule violated and where it lives.
- **Deterministic where possible.** Shell out to `ruff` / `biome` / `pytest` / etc. Only invoke Claude Code subprocess when AI is genuinely needed.
- **Cross-platform.** Tested on Windows Git Bash AND Linux.
- **Tier-aware.** Read `.workshop/config.toml` and adjust behavior accordingly.

## Phase 3 quality bar

Failures must be loud and specific (not "commit failed" black boxes). Each hook fires only when its preconditions are met. Per-hook toggles (in `[hooks]` config) work correctly.

See [`../docs/spec.md`](../docs/spec.md) §8 (Hook Catalog) for full hook specifications. See [`../plan.md`](../plan.md) §3 for Phase 3 success criteria.

# hooks/

Git hook bash scripts that `workshop init` installs into `.git/hooks/` of scaffolded projects. Joinery owns 4 hooks; the 5th (post-commit, for adversarial review) is managed by [roborev](https://github.com/roborev-dev/roborev) when installed.

## Hooks

```
hooks/
├── pre-commit          # lint + type-check on staged files + AGENTS.md mirror
├── pre-push            # refuses direct main pushes on production; reads reviews/ for critical findings
├── commit-msg          # Lore Protocol structure check; bot/daemon authors bypass
└── post-merge          # preflight refresh after pulling/merging
```

## Implementation principles

- **`set -euo pipefail`** at top of every script
- **Specific error messages** naming the rule violated and pointing to docs
- **Tier-aware** via `.workshop/config.toml` (read via Python tomllib in one call per hook)
- **Per-hook toggles** respected — each hook checks its `[hooks].<name>` flag
- **Cross-platform** — `python3` with `python` fallback for Windows Git Bash compatibility
- **Executable bit tracked** via git (chmod +x set; preserved across clones)

Each hook is under 50 lines of code (excluding comments). If you can't understand what a hook does in 30 seconds, refactor.

## What lives where

| Hook | Fires | Behavior |
|---|---|---|
| pre-commit | Before commit lands | Lint + type-check on staged files; mirrors CLAUDE.md to AGENTS.md |
| pre-push | Before push leaves machine | Refuses direct main on production; reads `reviews/` for critical findings |
| commit-msg | After commit message composed | Enforces Lore Protocol over threshold; bypasses bot authors |
| post-merge | After pull/merge | Quick lint check; surfaces dep changes |

See `docs/spec.md` §8 (Hook Catalog) for full specifications.

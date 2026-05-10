"""`workshop doctor` — verify workshop + project health.

Checks:
- Workshop config exists at ~/.config/joinery/ (informational)
- ccstatusline is configured (informational; can't fully verify without Claude Code)
- roborev is installed (informational; framework works without it via fallback)
- pipx joinery-cli version (informational)
- For a project: .workshop/config.toml valid, hooks installed, CLAUDE.md <-> AGENTS.md in sync,
  plan.md freshness for production tier
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import click

from joinery import __version__, git
from joinery.config import get_tier, read_config


def run_doctor(project_root: Path) -> None:
    """Run health checks and print results."""
    click.echo("Workshop:")
    workshop_dir = Path.home() / ".config" / "joinery"
    if (workshop_dir / "CLAUDE.md").is_file():
        click.echo("  ~/.config/joinery/         present")
    else:
        click.echo("  ~/.config/joinery/         MISSING (run `workshop setup` if available)")
    click.echo(f"  joinery-cli version        {__version__}")
    ccs_status = "found" if shutil.which("ccstatusline") else "not detected"
    click.echo(f"  ccstatusline               {ccs_status}")
    roborev_status = "found" if shutil.which("roborev") else "not installed (fallback active)"
    click.echo(f"  roborev                    {roborev_status}")
    click.echo("")

    config_path = project_root / ".workshop" / "config.toml"
    if not config_path.is_file():
        click.echo(f"Project ({project_root.name}):")
        click.echo("  Not a Joinery project — no .workshop/config.toml")
        click.echo("  Run `workshop init` to scaffold.")
        return

    click.echo(f"Project ({project_root.name}):")
    try:
        config = read_config(project_root)
        tier = get_tier(config)
        click.echo(f"  .workshop/config.toml      valid (tier={tier})")
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"  .workshop/config.toml      INVALID: {exc}")
        return

    # Hooks installed
    expected_hooks = ("pre-commit", "pre-push", "commit-msg", "post-merge")
    missing_hooks: list[str] = []
    for name in expected_hooks:
        hook_path = project_root / ".git" / "hooks" / name
        if not hook_path.is_file():
            missing_hooks.append(name)
    total = len(expected_hooks)
    found = total - len(missing_hooks)
    if not missing_hooks:
        click.echo(f"  .git/hooks/                {found}/{total} hooks installed")
    else:
        missing_list = ", ".join(missing_hooks)
        click.echo(f"  .git/hooks/                {found}/{total} (MISSING: {missing_list})")

    # CLAUDE.md <-> AGENTS.md sync
    claude = project_root / "CLAUDE.md"
    agents = project_root / "AGENTS.md"
    if claude.is_file() and agents.is_file():
        if claude.read_text(encoding="utf-8") == agents.read_text(encoding="utf-8"):
            click.echo("  CLAUDE.md <-> AGENTS.md    in sync")
        else:
            click.echo(
                "  CLAUDE.md <-> AGENTS.md    OUT OF SYNC (pre-commit hook will fix on next commit)"
            )

    # plan.md freshness on production tier
    plan_path = project_root / "plan.md"
    if plan_path.is_file() and tier == "production":
        mtime = datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC)
        age_days = (datetime.now(tz=UTC) - mtime).days
        if age_days <= 14:
            click.echo(f"  plan.md freshness          updated {age_days} day(s) ago")
        else:
            click.echo(
                f"  plan.md freshness          STALE ({age_days} days; production wants <=14)"
            )

    click.echo("")
    try:
        clean = git.is_clean(project_root)
        click.echo(f"  git status                 {'clean' if clean else 'dirty'}")
    except git.GitError:
        click.echo("  git status                 not a git repo")

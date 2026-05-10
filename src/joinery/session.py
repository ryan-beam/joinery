"""`workshop session start` and `workshop session end`.

These commands wrap the skills defined in skills/ (workshop-session-start.md
and workshop-session-end.md). The Python side handles deterministic preflight
checks; the skills handle the agent-driven explain-back and handover steps.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import click

from joinery import git
from joinery.config import get_tier, read_config


def session_start(project_root: Path) -> None:
    """Read HANDOVER.md, run preflight, print the session-start summary."""
    try:
        config = read_config(project_root)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    tier = get_tier(config)
    handover_path = project_root / "HANDOVER.md"

    click.echo(f"Workshop session start (tier: {tier})")
    click.echo("")

    if handover_path.is_file():
        click.echo("HANDOVER.md:")
        content = handover_path.read_text(encoding="utf-8")
        for line in content.splitlines()[:10]:
            click.echo(f"  {line}")
        click.echo("")
    else:
        click.echo("No HANDOVER.md yet (first session).")
        click.echo("")

    click.echo("Preflight:")
    try:
        clean = git.is_clean(project_root)
        click.echo(f"  git status:           {'clean' if clean else 'dirty (uncommitted changes)'}")
        click.echo(f"  current branch:       {git.current_branch(project_root)}")
    except git.GitError as exc:
        click.echo(f"  git:                  ERROR ({exc})")

    plan_path = project_root / "plan.md"
    if plan_path.is_file():
        mtime = datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC)
        age_days = (datetime.now(tz=UTC) - mtime).days
        warning = (
            " (production tier wants <=14 days)" if tier == "production" and age_days > 14 else ""
        )
        click.echo(f"  plan.md freshness:    updated {age_days} day(s) ago{warning}")

    click.echo("")
    click.echo("Workshop is open. Ready when you are.")


def session_end(project_root: Path) -> None:
    """Compose explain-back + handover + sq reconcile + token report.

    This Python entry point primarily prints a session-end framing. The actual
    explain-back and handover content is produced by the agent via the
    workshop-session-end skill (skills/workshop-session-end.md).
    """
    try:
        config = read_config(project_root)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    tier = get_tier(config)

    click.echo(f"Workshop session end (tier: {tier})")
    click.echo("")
    click.echo("The agent's workshop-session-end skill will:")
    click.echo("  1. Run /explain-back on this session's commits")
    click.echo("  2. Pause for the comprehension gate (you read, anything surprising = dig in)")
    click.echo("  3. Reconcile open side quests")
    click.echo("  4. Run /handover to overwrite HANDOVER.md")
    click.echo("  5. Prompt for primary/secondary classification")
    click.echo("  6. Print the per-phase token report from .workshop/usage.jsonl")
    click.echo("")
    click.echo("Invoke 'workshop session end' from inside Claude Code to trigger the skill.")

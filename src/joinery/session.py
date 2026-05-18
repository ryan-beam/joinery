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
    """Run deterministic branch-finishing checks + hand off to the orchestrator skill.

    This Python entry point produces the state snapshot the agent needs to
    drive the workshop-session-end orchestrator (skills/workshop-session-end.md):
    branch name, commits ahead, dirty state, open PR (if `gh` available),
    tier, and a reminder of the 7-phase ceremony.

    The agent runs the actual orchestration (verify tests, menu, explain-back,
    handover, learning) once invoked from Claude Code.
    """
    try:
        config = read_config(project_root)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    tier = get_tier(config)

    click.echo(f"Workshop session end (tier: {tier})")
    click.echo("")

    # --- Deterministic branch state snapshot ---
    click.echo("Branch state:")
    try:
        branch = git.current_branch(project_root)
        click.echo(f"  Current branch:    {branch}")
    except git.GitError as exc:
        click.echo(f"  Current branch:    ERROR ({exc})")
        branch = None

    main_branch = _read_main_branch(config)
    if branch and main_branch:
        try:
            ahead = _commits_ahead_of_main(project_root, branch, main_branch)
            click.echo(f"  Commits ahead of {main_branch}: {ahead}")
        except git.GitError as exc:
            click.echo(f"  Commits ahead:     ERROR ({exc})")

    try:
        clean = git.is_clean(project_root)
        click.echo(f"  Uncommitted:       {'none' if clean else 'YES — see git status'}")
    except git.GitError as exc:
        click.echo(f"  Uncommitted:       ERROR ({exc})")

    if branch and branch != main_branch:
        pr_info = _open_pr_for_branch(project_root, branch)
        if pr_info is not None:
            click.echo(f"  Open PR:           {pr_info}")
        else:
            click.echo("  Open PR:           none (or `gh` unavailable)")

    click.echo(f"  Tier:              {tier}")
    click.echo("")

    # --- Hand off to the agent ---
    click.echo("Agent orchestrator (7 phases): the workshop-session-end skill will")
    click.echo("walk you through:")
    click.echo("  1. Verify tests pass (gate — red = stop)")
    click.echo("  2. Detect branch state (already shown above)")
    click.echo("  3. Present the branch-finishing menu (merge / PR / keep / discard)")
    click.echo("  4. Execute your choice (production tier: /review gate before merge)")
    click.echo("  5. Comprehension gate via /explain-back")
    click.echo("  6. /handover overwrites HANDOVER.md")
    click.echo("  7. Side quest reconciliation + primary/secondary + token report")
    click.echo("")
    click.echo("Invoke 'workshop session end' from inside Claude Code (or type")
    click.echo("'wrap up this session') to trigger the agent orchestrator.")


def _read_main_branch(config: dict[str, object]) -> str:
    """Read the configured main-branch name from framework.config.toml, default 'main'."""
    git_section = config.get("git", {})
    if isinstance(git_section, dict):
        branching = git_section.get("branching", {})
        if isinstance(branching, dict):
            name = branching.get("main_branch")
            if isinstance(name, str) and name:
                return name
    return "main"


def _commits_ahead_of_main(project_root: Path, branch: str, main_branch: str) -> int:
    """Count commits on `branch` that are not on `origin/<main_branch>` (or local fallback)."""
    import subprocess

    for ref in (f"origin/{main_branch}", main_branch):
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", f"{ref}..HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            continue
        if result.returncode == 0:
            try:
                return int(result.stdout.strip())
            except ValueError:
                return 0
    return 0


def _open_pr_for_branch(project_root: Path, branch: str) -> str | None:
    """Return a one-line summary of any open PR for `branch`, or None if no `gh` or no PR."""
    import shutil
    import subprocess

    if shutil.which("gh") is None:
        return None
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "number,url",
                "--limit",
                "1",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    import json

    try:
        prs = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not prs:
        return None
    pr = prs[0]
    return f"#{pr['number']} (open) — {pr['url']}"

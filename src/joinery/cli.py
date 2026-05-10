"""Workshop CLI entry point.

Subcommands:
    workshop init <name> [--tier T] [--lang L] [--git/--no-git]
    workshop session start
    workshop session end
    workshop promote <project> --to <tier>
    workshop doctor
"""

from __future__ import annotations

from pathlib import Path

import click

from joinery import __version__
from joinery.doctor import run_doctor
from joinery.init import scaffold
from joinery.promote import promote_project
from joinery.session import session_end, session_start


@click.group(invoke_without_command=True)
@click.version_option(__version__, "-V", "--version")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Workshop — the Joinery framework's command-line tool."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command("init")
@click.argument("name", required=False)
@click.option(
    "--tier",
    type=click.Choice(["production", "standard", "sketch"], case_sensitive=False),
    help="Tier to initialize at. Prompted if omitted.",
)
@click.option(
    "--lang",
    type=click.Choice(["python", "typescript", "polyglot"], case_sensitive=False),
    help="Primary language hint for scaffolding. Auto-detected from cwd if omitted.",
)
@click.option("--git/--no-git", default=True, help="Initialize a git repo. Default: yes.")
@click.option("--path", type=click.Path(), help="Where to scaffold. Default: ./<name>.")
def init_command(
    name: str | None,
    tier: str | None,
    lang: str | None,
    git: bool,
    path: str | None,
) -> None:
    """Scaffold a new Joinery project.

    Interactive when flags are omitted; flag-driven for power users.

    \b
    Examples:
        workshop init my-project --tier production --lang python
        workshop init          # fully interactive
    """
    if name is None:
        name = click.prompt("Project name")
    if tier is None:
        tier = click.prompt(
            "Choose tier",
            type=click.Choice(["production", "standard", "sketch"], case_sensitive=False),
            default="standard",
            show_default=True,
        )
    if lang is None:
        lang = click.prompt(
            "Primary language? (python | typescript | polyglot)",
            type=click.Choice(["python", "typescript", "polyglot"], case_sensitive=False),
            default="python",
            show_default=True,
        )

    target = Path(path) if path else Path.cwd() / name

    click.echo(f"Creating {target}/")
    try:
        written = scaffold(
            target=target,
            project_name=name,
            tier=tier,
            language=lang,
            init_git=git,
        )
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc

    for rel in written[:20]:
        click.echo(f"  + {rel}")
    if len(written) > 20:
        click.echo(f"  ... and {len(written) - 20} more")

    click.echo("")
    click.echo("Bench is set up. Next:")
    click.echo(f"  cd {target.name}")
    click.echo("  workshop session start          # read HANDOVER, run preflight")
    click.echo("  /plan                           # draft your first plan with the agent")
    click.echo("")
    click.echo("Read CLAUDE.md and plan.md before your first session.")


@main.group("session")
def session_group() -> None:
    """Session start/end ritual."""


@session_group.command("start")
def session_start_command() -> None:
    """Read HANDOVER, run preflight, load context."""
    session_start(Path.cwd())


@session_group.command("end")
def session_end_command() -> None:
    """Compose explain-back + handover + sq reconcile + token report."""
    session_end(Path.cwd())


@main.command("promote")
@click.argument("project", required=False)
@click.option(
    "--to",
    "target_tier",
    type=click.Choice(["standard", "production"], case_sensitive=False),
    required=True,
    help="Tier to promote to. Demotion is not supported.",
)
def promote_command(project: str | None, target_tier: str) -> None:
    """Promote a Joinery project to a higher tier (sketch -> standard -> production)."""
    target = Path(project) if project else Path.cwd()
    promote_project(target, target_tier)


@main.command("doctor")
@click.option("--project", type=click.Path(exists=True), help="Project to check. Default: cwd.")
def doctor_command(project: str | None) -> None:
    """Verify workshop + project health (statusline, hooks, roborev, config sanity)."""
    target = Path(project) if project else Path.cwd()
    run_doctor(target)

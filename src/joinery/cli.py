"""Workshop CLI entry point.

Subcommands:
    workshop init <name> [--tier T] [--lang L] [--git/--no-git] [--dry-run]
    workshop adopt [--tier T] [--lang L] [--path P] [--force] [--no-hooks] [--dry-run]
    workshop rollback [--path P] [--keep-files] [--yes]
    workshop diff [--path P]
    workshop update [--path P] [--dry-run] [--yes]
    workshop session start
    workshop session end
    workshop promote <project> --to <tier>
    workshop doctor
"""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from joinery import __version__
from joinery.adopt import AdoptResult, AlreadyAdoptedError, adopt, language_at_adopt
from joinery.diff import DiffReport, NotAdoptedError, diff_managed_files
from joinery.doctor import run_doctor
from joinery.init import scaffold
from joinery.preadopt import UnsafeAdoptError
from joinery.promote import promote_project
from joinery.rollback import NoTransactionError, RollbackResult, rollback
from joinery.session import session_end, session_start
from joinery.update import UpdateResult, apply_updates


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
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview what would be written without touching the filesystem.",
)
def init_command(
    name: str | None,
    tier: str | None,
    lang: str | None,
    git: bool,
    path: str | None,
    dry_run: bool,
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

    if dry_run:
        click.echo(f"DRY RUN — Would create {target}/ (no files written)")
    else:
        click.echo(f"Creating {target}/")
    try:
        written = scaffold(
            target=target,
            project_name=name,
            tier=tier,
            language=lang,
            init_git=git,
            dry_run=dry_run,
        )
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc

    for rel in written[:20]:
        click.echo(f"  + {rel}")
    if len(written) > 20:
        click.echo(f"  ... and {len(written) - 20} more")

    if dry_run:
        click.echo("")
        click.echo("Dry run complete — re-run without --dry-run to write these files.")
        return

    click.echo("")
    click.echo("Bench is set up. Next:")
    click.echo(f"  cd {target.name}")
    click.echo("  workshop session start          # read HANDOVER, run preflight")
    click.echo("  /plan                           # draft your first plan with the agent")
    click.echo("")
    click.echo("Read CLAUDE.md and plan.md before your first session.")


@main.command("adopt")
@click.option(
    "--tier",
    type=click.Choice(["production", "standard", "sketch"], case_sensitive=False),
    help="Tier to adopt at. Prompted if omitted.",
)
@click.option(
    "--lang",
    type=click.Choice(["python", "typescript", "polyglot"], case_sensitive=False),
    help="Primary language hint. Auto-detected from target if omitted.",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False),
    help="Target directory to adopt. Default: current working directory.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing framework files. Destructive — review the diff before committing.",
)
@click.option(
    "--no-hooks",
    "skip_hooks",
    is_flag=True,
    default=False,
    help="Skip installing git hooks (useful when adopting in CI or non-git contexts).",
)
@click.option(
    "--allow-dirty",
    is_flag=True,
    default=False,
    help="Proceed even if the working tree has uncommitted changes (review the diff carefully).",
)
@click.option(
    "--no-scan",
    "skip_scan",
    is_flag=True,
    default=False,
    help="Skip the pre-adopt safety scan entirely. Not recommended for normal use.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview what would be written without touching the filesystem.",
)
def adopt_command(
    tier: str | None,
    lang: str | None,
    path: str | None,
    force: bool,
    skip_hooks: bool,
    allow_dirty: bool,
    skip_scan: bool,
    dry_run: bool,
) -> None:
    """Overlay Joinery onto an existing codebase.

    Run from inside the target directory, or pass --path. Adopt does not
    overwrite existing files by default; pass --force if you want to replace
    them. Adopt does not auto-commit — stage and review the changes yourself.

    \b
    Examples:
        cd my-existing-project
        workshop adopt --tier production --lang python
        workshop adopt --path ../other-repo --tier standard
    """
    target = Path(path).resolve() if path else Path.cwd()

    if tier is None:
        tier = click.prompt(
            "Choose tier",
            type=click.Choice(["production", "standard", "sketch"], case_sensitive=False),
            default="standard",
            show_default=True,
        )

    try:
        language = language_at_adopt(target, lang)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    header = "DRY RUN — would adopt" if dry_run else "Adopting"
    click.echo(f"{header} Joinery into {target}/ (tier={tier}, lang={language})")
    if force:
        click.echo("  --force: existing framework files will be overwritten.")

    try:
        result = adopt(
            target=target,
            tier=tier,
            language=language,
            force=force,
            install_hooks=not skip_hooks,
            allow_dirty=allow_dirty,
            skip_scan=skip_scan,
            dry_run=dry_run,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    except AlreadyAdoptedError as exc:
        raise click.ClickException(str(exc)) from exc
    except UnsafeAdoptError as exc:
        click.echo("")
        click.echo("Pre-adopt safety scan failed:", err=True)
        for err in exc.report.errors:
            click.echo(f"  ERROR: {err}", err=True)
        for warning in exc.report.warnings:
            click.echo(f"  warning: {warning}", err=True)
        click.echo("")
        click.echo("Override flags:", err=True)
        click.echo("  --allow-dirty   bypass the dirty-tree check", err=True)
        click.echo("  --no-scan       skip the entire scan (not recommended)", err=True)
        raise click.ClickException("Adoption halted by safety scan.") from exc

    _print_adopt_summary(result, skip_hooks=skip_hooks)


def _print_adopt_summary(result: AdoptResult, skip_hooks: bool) -> None:
    """Print human-readable summary of an adopt() call."""
    all_written = list(result.written) + list(result.hooks_written)
    all_preserved = list(result.preserved) + list(result.hooks_preserved)

    if result.safety_report.warnings or result.safety_report.info:
        click.echo("")
        click.echo("Safety scan:")
        for warning in result.safety_report.warnings:
            click.echo(f"  warning: {warning}")
        for note in result.safety_report.info:
            click.echo(f"  note: {note}")

    if result.hooks_backup is not None:
        click.echo("")
        click.echo(f"Backed up existing hooks to: {result.hooks_backup}")

    written_verb = "Would write" if result.dry_run else "Wrote"
    preserved_verb = "Would preserve" if result.dry_run else "Preserved"

    if all_written:
        click.echo("")
        click.echo(f"{written_verb} {len(all_written)} file(s):")
        for rel in all_written[:20]:
            click.echo(f"  + {rel}")
        if len(all_written) > 20:
            click.echo(f"  ... and {len(all_written) - 20} more")

    if all_preserved:
        click.echo("")
        click.echo(f"{preserved_verb} {len(all_preserved)} existing file(s):")
        for rel in all_preserved[:10]:
            click.echo(f"  = {rel}")
        if len(all_preserved) > 10:
            click.echo(f"  ... and {len(all_preserved) - 10} more")
        click.echo("  (pass --force to overwrite)")

    if not result.is_git_repo and not skip_hooks:
        click.echo("")
        click.echo("Note: target is not a git repository. Hooks were not installed.")
        click.echo("      Run `git init` and `workshop adopt --force` to install hooks later,")
        click.echo("      or copy hooks manually from the joinery repo's hooks/ directory.")

    if result.dry_run:
        click.echo("")
        click.echo("Dry run complete — re-run without --dry-run to apply.")

    click.echo("")
    click.echo("Adoption complete. Next:")
    click.echo("  git status                # review the new files")
    click.echo("  git add -A && git commit -m 'joinery: adopt framework'")
    click.echo("  workshop doctor           # verify the install")


@main.command("rollback")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False),
    help="Project to roll back. Default: current working directory.",
)
@click.option(
    "--keep-files",
    is_flag=True,
    default=False,
    help="Restore hooks but leave written files in place.",
)
@click.option(
    "--yes", "skip_confirm", is_flag=True, default=False, help="Skip confirmation prompt."
)
def rollback_command(path: str | None, keep_files: bool, skip_confirm: bool) -> None:
    """Undo the most recent Joinery transaction.

    Reads the most recent record under `.joinery/transactions/`, deletes every
    file it wrote (unless --keep-files), restores any hooks from the recorded
    backup, and removes the transaction record. Only the most recent operation
    is undone — older state is git's job.
    """
    target = Path(path).resolve() if path else Path.cwd()

    if not skip_confirm:
        if not click.confirm(
            f"Roll back the most recent Joinery transaction in {target}/?",
            default=False,
        ):
            click.echo("Aborted.")
            return

    try:
        result = rollback(target, keep_files=keep_files)
    except NoTransactionError as exc:
        raise click.ClickException(str(exc)) from exc

    _print_rollback_summary(result, keep_files=keep_files)


def _print_rollback_summary(result: RollbackResult, keep_files: bool) -> None:
    """Print human-readable summary of a rollback() call."""
    txn = result.transaction
    if txn is None:
        # rollback() never returns with txn=None — it raises NoTransactionError first.
        return
    click.echo("")
    click.echo(f"Rolled back: {txn.mode} (tier={txn.tier}, {txn.timestamp})")

    if keep_files:
        click.echo("  --keep-files: written files left in place.")
    elif result.deleted_files:
        click.echo("")
        click.echo(f"Deleted {len(result.deleted_files)} file(s):")
        for rel in result.deleted_files[:20]:
            click.echo(f"  - {rel}")
        if len(result.deleted_files) > 20:
            click.echo(f"  ... and {len(result.deleted_files) - 20} more")

    if result.missing_files:
        click.echo("")
        click.echo(f"{len(result.missing_files)} file(s) already missing (skipped):")
        for rel in result.missing_files[:10]:
            click.echo(f"  ? {rel}")

    if result.restored_hooks:
        click.echo("")
        click.echo(f"Restored {len(result.restored_hooks)} hook(s) from backup:")
        for name in result.restored_hooks:
            click.echo(f"  > {name}")

    if result.transaction_path is not None:
        click.echo("")
        click.echo(f"Transaction record removed: {result.transaction_path.name}")


@main.command("diff")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False),
    help="Project to inspect. Default: current working directory.",
)
def diff_command(path: str | None) -> None:
    """Show drift between current managed files and current Joinery templates.

    Read-only. Compares every rendered managed file (CLAUDE.md, plan.md,
    learning/, ADR, .workshop/config.toml) against what Joinery would produce
    today. Reports per-file status plus a unified diff for drifted files.
    """
    target = Path(path).resolve() if path else Path.cwd()
    try:
        report = diff_managed_files(target)
    except NotAdoptedError as exc:
        raise click.ClickException(str(exc)) from exc
    _print_diff_report(report)


def _print_diff_report(report: DiffReport) -> None:
    """Print a diff report to stdout."""
    if report.manifest_version != report.current_version:
        click.echo(
            f"Joinery version: manifest={report.manifest_version} -> "
            f"current={report.current_version}"
        )

    if not report.has_drift:
        click.echo("No drift. Managed files match current templates.")
        return

    if report.drifted:
        click.echo("")
        click.echo(f"Drifted ({len(report.drifted)}):")
        for entry in report.drifted:
            click.echo(f"  ~ {entry.rel_path}")
        click.echo("")
        for entry in report.drifted:
            click.echo(f"=== {entry.rel_path} ===")
            click.echo(entry.unified_diff)

    if report.missing:
        click.echo("")
        click.echo(f"Missing ({len(report.missing)}) — managed but not on disk:")
        for entry in report.missing:
            click.echo(f"  ! {entry.rel_path}")

    if report.clean:
        click.echo("")
        click.echo(f"Clean: {len(report.clean)} file(s) match current templates.")

    click.echo("")
    click.echo("Run `workshop update` to apply.")


@main.command("update")
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False),
    help="Project to update. Default: current working directory.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview what would change without writing.",
)
@click.option(
    "--yes",
    "skip_confirm",
    is_flag=True,
    default=False,
    help="Skip the confirmation prompt.",
)
def update_command(path: str | None, dry_run: bool, skip_confirm: bool) -> None:
    """Apply pending drift — bring managed files in sync with current templates.

    Reads the diff via `workshop diff` machinery and writes the freshly-rendered
    template content for any drifted or missing managed file. On success
    refreshes `.workshop/answers.toml` with the current Joinery version and
    appends a new transaction log entry.
    """
    target = Path(path).resolve() if path else Path.cwd()

    try:
        # Run a diff first so the user sees what will change before confirming.
        report = diff_managed_files(target)
    except NotAdoptedError as exc:
        raise click.ClickException(str(exc)) from exc

    pending = list(report.drifted) + list(report.missing)
    if not pending:
        click.echo("No drift. Nothing to update.")
        return

    click.echo(f"Pending updates: {len(pending)}")
    for entry in pending:
        marker = "~" if entry.status == "drifted" else "!"
        click.echo(f"  {marker} {entry.rel_path}")

    if dry_run:
        click.echo("")
        click.echo("Dry run — re-run without --dry-run to apply.")
        return

    if not skip_confirm and not click.confirm("Apply these updates?", default=False):
        click.echo("Aborted.")
        return

    result = apply_updates(target, dry_run=False)
    _print_update_summary(result)


def _print_update_summary(result: UpdateResult) -> None:
    """Print human-readable summary of an apply_updates() call."""
    click.echo("")
    click.echo(
        f"Updated {len(result.applied)} file(s) "
        f"(joinery {result.from_version} -> {result.to_version})"
    )
    for rel in result.applied[:20]:
        click.echo(f"  ~ {rel}")
    if len(result.applied) > 20:
        click.echo(f"  ... and {len(result.applied) - 20} more")


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


@main.command("setup")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Install without prompting. For CI / scripted use.",
)
def setup_command(yes: bool) -> None:
    """One-time global setup: install external tools Joinery integrates with.

    Currently installs roborev (the adversarial review engine) if not present.
    Cross-platform: tries the native package manager first (brew on macOS/Linux,
    winget/scoop on Windows), then a universal curl install script. Each attempt
    fails gracefully — if all fail, you get a clear next-step message.

    Idempotent: re-running after success is a no-op.
    """
    from joinery.setup import format_failure_help, run_setup

    click.echo("Workshop setup")
    click.echo("==============")
    click.echo("")

    if shutil.which("roborev"):
        click.echo("roborev:        already installed (skipping)")
        click.echo("")
        click.echo("Setup complete. `workshop doctor` should now show roborev: found.")
        return

    click.echo("roborev:        not installed")
    click.echo("")
    click.echo("Joinery's adversarial review (auto-fire on every commit) depends on")
    click.echo("roborev. The framework still works without it via Claude Code's built-in")
    click.echo("`/review` skill, but you'd have to invoke review manually each time.")
    click.echo("")

    if not yes:
        if not click.confirm("Install roborev now?", default=True):
            click.echo("")
            click.echo("Skipped. Re-run `workshop setup` any time to install.")
            return

    click.echo("")
    click.echo("Attempting install (cross-platform, multi-strategy)...")
    click.echo("")
    # If we're inside a Joinery project (current dir has .git AND .workshop),
    # also run `roborev init` after a successful install. Otherwise just install
    # globally and let the user run `roborev init` per-project later.
    cwd = Path.cwd()
    project_root = cwd if (cwd / ".git").is_dir() and (cwd / ".workshop").is_dir() else None
    result = run_setup(assume_yes=True, project_root=project_root)

    for attempt in result.attempts:
        if not attempt.available:
            click.echo(f"  - {attempt.label}: skipped (prereq missing)")
        elif attempt.success:
            click.echo(f"  - {attempt.label}: SUCCESS")
        else:
            err = attempt.error.strip().splitlines()[0] if attempt.error.strip() else "non-zero exit"
            click.echo(f"  - {attempt.label}: failed ({err})")

    click.echo("")
    if result.roborev_installed:
        click.echo("roborev installed successfully.")
        if result.roborev_init_run:
            click.echo("roborev init: post-commit hook installed in this project.")
        elif project_root is not None:
            click.echo(
                f"roborev init: failed in this project ({result.roborev_init_error}). "
                "Run `roborev init` manually."
            )
        else:
            click.echo(
                "Not inside a Joinery project — run `roborev init` from your "
                "project root to install the post-commit hook there."
            )
        click.echo("")
        click.echo("Next: `workshop doctor` to verify daemon health.")
        click.echo("From the next commit forward, roborev auto-reviews every commit.")
    else:
        click.echo(format_failure_help(result))


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

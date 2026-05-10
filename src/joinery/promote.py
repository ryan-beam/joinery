"""`workshop promote` — upgrade a scaffold to a higher tier in place.

Tier promotion is additive: sketch -> standard adds tests/, reviews/,
missing skills/hooks, and updates config.toml. Demotion is intentionally
not supported (if a project no longer needs production rigor, archive it).
"""

from __future__ import annotations

from pathlib import Path

import click

from joinery import git
from joinery.config import get_tier, read_config
from joinery.templates import copy_template, render_context, select_config_template

TIER_ORDER = {"sketch": 0, "standard": 1, "production": 2}


def promote_project(project_root: Path, target_tier: str) -> None:
    """Promote a project's scaffold to the target tier."""
    try:
        config = read_config(project_root)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    current_tier = get_tier(config)
    if TIER_ORDER[target_tier] <= TIER_ORDER[current_tier]:
        raise click.ClickException(
            f"Cannot promote: project is already at '{current_tier}' tier. "
            f"Demotion is not supported."
        )

    project_name = config.get("meta", {}).get("project_name", project_root.name)
    language = config.get("lang", {}).get("primary", "python")
    ctx = render_context(project_name=project_name, tier=target_tier, language=language)

    # Update framework.config.toml to the target tier
    new_config_src = select_config_template(target_tier)
    new_config_dest = project_root / ".workshop" / "config.toml"
    copy_template(new_config_src, new_config_dest, ctx)
    click.echo(f"Updated .workshop/config.toml to tier={target_tier}")

    # Add missing directories (tests/, reviews/, docs/operations/, docs/reference/ on production)
    additions = []
    if target_tier in ("standard", "production"):
        for dirname in ("tests", "reviews"):
            d = project_root / dirname
            if not d.exists():
                d.mkdir(parents=True)
                (d / ".gitkeep").write_text("", encoding="utf-8")
                additions.append(str(d.relative_to(project_root)))
    if target_tier == "production":
        for dirname in ("docs/operations", "docs/reference"):
            d = project_root / dirname
            if not d.exists():
                d.mkdir(parents=True)
                (d / ".gitkeep").write_text("", encoding="utf-8")
                additions.append(str(d.relative_to(project_root)))

    # Re-install hooks if missing (some are off in sketch tier)
    from joinery.paths import hooks_dir

    hooks_src = hooks_dir()
    for hook_name in ("pre-commit", "pre-push", "commit-msg", "post-merge"):
        hook_target = project_root / ".git" / "hooks" / hook_name
        hook_source = hooks_src / hook_name
        if hook_source.is_file() and not hook_target.is_file():
            git.install_hook(hook_source, project_root)
            additions.append(f".git/hooks/{hook_name}")

    if additions:
        click.echo("Added:")
        for path in additions:
            click.echo(f"  + {path}")

    # Commit the promotion
    try:
        git.add_all(project_root)
        commit_msg = (
            f"workshop: promoted from {current_tier} to {target_tier}\n\n"
            f"Additive scaffold upgrade. New defaults applied from "
            f"templates/config/framework.config.toml.{target_tier}."
        )
        git.commit(project_root, commit_msg)
        click.echo(f"Promoted from {current_tier} to {target_tier}. Commit landed.")
    except git.GitError as exc:
        click.echo(f"Promotion files written; git commit failed: {exc}")

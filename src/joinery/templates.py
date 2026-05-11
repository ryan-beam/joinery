"""Template rendering for scaffolded projects.

Templates use Jinja2 `{{var}}` syntax. The workshop CLI reads templates from
the framework's `templates/` directory and renders them into the target project
with project-specific values (name, tier, language, dates, version).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jinja2

from joinery import __version__ as joinery_version
from joinery.paths import templates_dir


def render_context(project_name: str, tier: str, language: str) -> dict[str, Any]:
    """Build the variable context that templates can reference."""
    now = datetime.now(tz=UTC)
    return {
        "project_name": project_name,
        "tier": tier,
        "language": language,
        "init_at": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "joinery_version": joinery_version,
        "branch": "main",
        "week": now.strftime("%G-W%V"),
        "last_session_end": now.isoformat(timespec="seconds"),
    }


def _render_text(content: str, ctx: dict[str, Any]) -> str:
    """Render a single template string. Uses Jinja2 with autoescape disabled
    since these are markdown/TOML, not HTML."""
    env = jinja2.Environment(
        autoescape=False,  # noqa: S701 — templates are markdown/TOML, not HTML
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    template = env.from_string(content)
    return template.render(**ctx)


def copy_template(
    source: Path,
    target: Path,
    ctx: dict[str, Any],
    *,
    skip_existing: bool = False,
    dry_run: bool = False,
) -> bool:
    """Copy a single template file from source to target, rendering placeholders.

    Returns True if the file was written (or *would be* written under dry_run),
    False if it was preserved (only possible when skip_existing=True and target
    already exists). When `dry_run=True`, no filesystem mutation occurs, but
    the return value still reflects what would have happened.
    """
    if skip_existing and target.exists():
        return False
    if dry_run:
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_text(encoding="utf-8")
    rendered = _render_text(content, ctx)
    target.write_text(rendered, encoding="utf-8")
    return True


def copy_tree(
    source_dir: Path,
    target_dir: Path,
    ctx: dict[str, Any],
    *,
    skip_existing: bool = False,
    dry_run: bool = False,
) -> tuple[list[Path], list[Path]]:
    """Recursively copy a template tree into target_dir, rendering each file.

    Returns (written, preserved): both lists hold paths relative to target_dir.
    The preserved list is always empty when skip_existing=False. Under
    `dry_run=True`, no files are written but the return value reflects what
    would have happened.
    """
    written: list[Path] = []
    preserved: list[Path] = []
    for source_file in sorted(source_dir.rglob("*")):
        if not source_file.is_file():
            continue
        relative = source_file.relative_to(source_dir)
        # Strip ".template" and ".starter" / ".global" suffixes from output filename.
        # Example: CLAUDE.md.starter -> CLAUDE.md; plan.md.template -> plan.md
        target_name = _strip_template_suffix(relative.name)
        target_file = target_dir / relative.with_name(target_name)
        rel_out = target_file.relative_to(target_dir)
        if copy_template(
            source_file, target_file, ctx, skip_existing=skip_existing, dry_run=dry_run
        ):
            written.append(rel_out)
        else:
            preserved.append(rel_out)
    return written, preserved


def _strip_template_suffix(filename: str) -> str:
    for suffix in (".template", ".starter", ".global"):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return filename


def select_config_template(tier: str) -> Path:
    """Return the path to the tier-appropriate config.toml template."""
    name = f"framework.config.toml.{tier}"
    path = templates_dir() / "config" / name
    if not path.is_file():
        raise FileNotFoundError(f"Config template not found for tier {tier!r}: {path}")
    return path


def copy_static(source: Path, target: Path, *, dry_run: bool = False) -> None:
    """Copy a file without template rendering. No-op when dry_run=True."""
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

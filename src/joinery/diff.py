"""`workshop diff` — compute drift between current managed files and current templates.

For each rendered file Joinery would currently produce in a project, compare
the on-disk content against the would-be content. Surface the difference as a
unified diff per file plus a status: clean, drifted, missing, or template-only.

Stable time-based variables (`init_at`, `date`, `last_session_end`, `week`) are
sourced from the manifest's `created_at` so the diff does not spuriously show
drift just because clocks moved forward. `joinery_version` is the CURRENT
version — version-bump drift in `managed-by` markers is real drift the user
should see and update.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from joinery import __version__
from joinery.init import PROJECT_TEMPLATES, _strip_template_suffix
from joinery.manifest import Manifest, read_manifest
from joinery.paths import templates_dir
from joinery.templates import render_template_file, select_config_template

FileStatus = Literal["clean", "drifted", "missing"]


class NotAdoptedError(RuntimeError):
    """Raised when diff/update is asked for a target with no manifest."""


@dataclass
class FileDiff:
    """Per-file drift entry from `diff_managed_files`."""

    rel_path: str
    status: FileStatus
    unified_diff: str = ""


@dataclass
class DiffReport:
    """Aggregate result of `diff_managed_files`."""

    diffs: list[FileDiff] = field(default_factory=list)
    manifest_version: str = ""
    current_version: str = __version__

    @property
    def drifted(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == "drifted"]

    @property
    def missing(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == "missing"]

    @property
    def clean(self) -> list[FileDiff]:
        return [d for d in self.diffs if d.status == "clean"]

    @property
    def has_drift(self) -> bool:
        return (
            bool(self.drifted)
            or bool(self.missing)
            or self.manifest_version != self.current_version
        )


def diff_managed_files(target: Path) -> DiffReport:
    """Compute drift between current managed files and current templates.

    Raises:
        NotAdoptedError: if `target` has no `.workshop/answers.toml`.
    """
    manifest = read_manifest(target)
    if manifest is None:
        raise NotAdoptedError(
            f"No `.workshop/answers.toml` in {target}. "
            f"Run `workshop adopt` or `workshop init` first."
        )

    expected = render_managed_state(manifest)
    report = DiffReport(manifest_version=manifest.joinery_version)

    for rel_path in sorted(expected):
        expected_content = expected[rel_path]
        file_path = target / rel_path
        if not file_path.is_file():
            report.diffs.append(FileDiff(rel_path=rel_path, status="missing"))
            continue
        on_disk = file_path.read_text(encoding="utf-8")
        if on_disk == expected_content:
            report.diffs.append(FileDiff(rel_path=rel_path, status="clean"))
            continue
        diff_text = "".join(
            difflib.unified_diff(
                on_disk.splitlines(keepends=True),
                expected_content.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            )
        )
        report.diffs.append(FileDiff(rel_path=rel_path, status="drifted", unified_diff=diff_text))

    return report


def render_managed_state(manifest: Manifest) -> dict[str, str]:
    """Return rel_path → expected content for each RENDERED managed file.

    Non-rendered managed files (hooks, skills, .workshop/usage.jsonl,
    .workshop/tier.lock, .workshop/answers.toml) are excluded — their content
    doesn't drift through template changes, and answers.toml is itself the
    source of truth.
    """
    ctx = _stable_diff_context(manifest)
    src_templates = templates_dir()
    rendered: dict[str, str] = {}

    for tpl_name in PROJECT_TEMPLATES:
        src = src_templates / tpl_name
        if not src.is_file():
            continue
        output_name = _strip_template_suffix(tpl_name)
        rendered[output_name] = render_template_file(src, ctx)

    learning_src = src_templates / "learning"
    if learning_src.is_dir():
        for source_file in sorted(learning_src.rglob("*")):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(learning_src)
            output_name = _strip_template_suffix(relative.name)
            output_path = Path("learning") / relative.with_name(output_name)
            rendered[output_path.as_posix()] = render_template_file(source_file, ctx)

    adr_src = src_templates / "docs" / "decisions" / "0001-tier-selection.md.template"
    if adr_src.is_file():
        rendered["docs/decisions/0001-tier-selection.md"] = render_template_file(adr_src, ctx)

    config_src = select_config_template(manifest.tier)
    rendered[".workshop/config.toml"] = render_template_file(config_src, ctx)

    return rendered


def _stable_diff_context(manifest: Manifest) -> dict[str, Any]:
    """Render context for diff/update: stable time vars, current joinery_version.

    Time-based vars (`init_at`, `date`, `last_session_end`, `week`) come from
    `manifest.created_at` so the diff does not show spurious drift just
    because time has passed. `joinery_version` is CURRENT — version-bump drift
    in `managed-by` markers is genuine drift, not noise.
    """
    created_at = manifest.created_at or datetime.now(tz=UTC).isoformat(timespec="seconds")
    try:
        dt = datetime.fromisoformat(created_at)
    except ValueError:
        dt = datetime.now(tz=UTC)
    return {
        "project_name": manifest.project_name,
        "tier": manifest.tier,
        "language": manifest.language,
        "init_at": created_at,
        "date": dt.date().isoformat(),
        "joinery_version": __version__,
        "branch": "main",
        "week": dt.strftime("%G-W%V"),
        "last_session_end": created_at,
    }

"""`workshop update` — apply pending drift to bring managed files in sync.

Reads the current diff via `diff.diff_managed_files()`, and for each
`drifted` or `missing` file writes the freshly-rendered template content to
disk. On success, writes a new transaction log entry recording the update
and refreshes the manifest with the current Joinery version.

`workshop update` is the natural counterpart to `workshop diff`: diff shows
you what would change; update applies it. Both bound to managed files only —
preserved files and user-owned content are never touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from joinery import __version__
from joinery.diff import DiffReport, FileDiff, diff_managed_files, render_managed_state
from joinery.manifest import Manifest, read_manifest, write_manifest
from joinery.transactions import Transaction, write_transaction


@dataclass
class UpdateResult:
    """Outcome of an apply_updates() call."""

    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    dry_run: bool = False
    from_version: str = ""
    to_version: str = __version__
    report: DiffReport | None = None


def apply_updates(
    target: Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    only: list[str] | None = None,
) -> UpdateResult:
    """Apply drift to managed files.

    Args:
        target: Project root.
        force: Reserved for future conflict-resolution use; currently every
            drifted file is applied. (User-edit detection happens here later.)
        dry_run: If True, compute what would change but don't write.
        only: Optional list of relative paths. If provided, restrict updates
            to those paths.

    Returns:
        UpdateResult listing what was applied, what was skipped, and the
        underlying DiffReport for further inspection.
    """
    manifest = read_manifest(target)
    if manifest is None:
        from joinery.diff import NotAdoptedError  # local import to share message

        raise NotAdoptedError(
            f"No `.workshop/answers.toml` in {target}. "
            f"Run `workshop adopt` or `workshop init` first."
        )

    report = diff_managed_files(target)
    expected = render_managed_state(manifest)

    result = UpdateResult(dry_run=dry_run, from_version=manifest.joinery_version, report=report)

    candidates: list[FileDiff] = list(report.drifted) + list(report.missing)
    for entry in candidates:
        if only is not None and entry.rel_path not in only:
            result.skipped.append(entry.rel_path)
            continue
        if not dry_run:
            _write_one(target, entry.rel_path, expected[entry.rel_path])
        result.applied.append(entry.rel_path)

    # `force` is reserved for future user-edit detection; for now it's a no-op
    # so the API matches the planned conflict-resolution flow.
    _ = force

    if not dry_run and result.applied:
        updated_manifest = Manifest(
            project_name=manifest.project_name,
            tier=manifest.tier,
            language=manifest.language,
            mode=manifest.mode,
            joinery_version=__version__,
            managed_files=manifest.managed_files,
            preserved_files=manifest.preserved_files,
            hooks_installed=manifest.hooks_installed,
            hooks_preserved=manifest.hooks_preserved,
            created_at=manifest.created_at,
        )
        write_manifest(target, updated_manifest)

        txn = Transaction(
            mode=manifest.mode,
            tier=manifest.tier,
            language=manifest.language,
            project_name=manifest.project_name,
            written_files=list(result.applied),
            hooks_installed=list(manifest.hooks_installed),
        )
        write_transaction(target, txn)

    return result


def _write_one(target: Path, rel_path: str, content: str) -> None:
    """Write a single file under `target`, creating parents if needed."""
    file_path = target / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

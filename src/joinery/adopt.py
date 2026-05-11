"""`workshop adopt` — overlay the Joinery framework onto an existing codebase.

Where `init` requires an empty target directory and scaffolds a fresh project,
`adopt` is designed for mid-project adoption: the target already has source
files, possibly already has CLAUDE.md or AGENTS.md, and almost certainly has
a git repo with its own history.

Default behavior is non-destructive: any file that already exists is preserved
and logged, only missing files are written. `--force` opts into overwriting.

Adopt does NOT auto-commit. The user stages and commits the new files
themselves so the adoption lands in their normal review flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from joinery.init import (
    install_hooks_into,
    install_skills,
    write_learning_module,
    write_project_files,
    write_tier_adr,
    write_workshop_state,
)
from joinery.lang import Language, detect_language
from joinery.manifest import Manifest, write_manifest
from joinery.preadopt import PreAdoptReport, UnsafeAdoptError, backup_hooks, scan
from joinery.templates import render_context


@dataclass
class AdoptResult:
    """Summary of what an adopt() call did."""

    written: list[Path] = field(default_factory=list)
    preserved: list[Path] = field(default_factory=list)
    hooks_written: list[Path] = field(default_factory=list)
    hooks_preserved: list[Path] = field(default_factory=list)
    is_git_repo: bool = True
    hooks_skipped: bool = False
    safety_report: PreAdoptReport = field(default_factory=PreAdoptReport)
    hooks_backup: Path | None = None


class AlreadyAdoptedError(RuntimeError):
    """Raised when adopting a target that already has .workshop/tier.lock."""


def adopt(
    target: Path,
    *,
    tier: str,
    language: str,
    force: bool = False,
    install_hooks: bool = True,
    allow_dirty: bool = False,
    skip_scan: bool = False,
) -> AdoptResult:
    """Overlay Joinery onto an existing codebase at `target`.

    Args:
        target: Existing directory to adopt. Must exist and be non-empty.
        tier: One of "production", "standard", "sketch".
        language: One of "python", "typescript", "polyglot".
        force: If True, overwrite existing files. Default: preserve them.
        install_hooks: If True (default) and target is a git repo, install
            framework hooks. Existing hooks are backed up and preserved
            unless force=True.
        allow_dirty: If True, skip the dirty-tree check from the pre-adopt
            scan. Default: refuse adoption on a dirty working tree so the
            resulting diff is reviewable.
        skip_scan: If True, skip the pre-adopt safety scan entirely. Useful
            for CI and recovery scenarios; not recommended for normal use.

    Returns:
        AdoptResult summarizing what was written, preserved, and skipped,
        plus the pre-adopt safety report and the hook backup path (if any).

    Raises:
        FileNotFoundError: target does not exist.
        ValueError: target exists but is empty (use `init` instead).
        AlreadyAdoptedError: target already has .workshop/tier.lock and
            force is False.
        UnsafeAdoptError: pre-adopt scan found blocking issues and no
            override flag was passed.
    """
    if not target.exists():
        raise FileNotFoundError(f"Directory `{target}` does not exist.")
    if not target.is_dir():
        raise NotADirectoryError(f"`{target}` exists but is not a directory.")
    if not any(target.iterdir()):
        raise ValueError(
            f"Directory `{target}` is empty. Use `workshop init` for greenfield projects."
        )

    tier_lock = target / ".workshop" / "tier.lock"
    if tier_lock.exists() and not force:
        existing = tier_lock.read_text(encoding="utf-8").strip()
        raise AlreadyAdoptedError(
            f"`{target}` is already adopted (tier={existing}). "
            f"Use --force to overwrite framework files."
        )

    is_git_repo = (target / ".git").is_dir()
    skip_existing = not force

    report = PreAdoptReport()
    if not skip_scan:
        report = scan(target, install_hooks=install_hooks)
        if report.has_errors and not _all_errors_overridden(report, allow_dirty=allow_dirty):
            raise UnsafeAdoptError(report)

    project_name = target.resolve().name
    ctx = render_context(project_name=project_name, tier=tier, language=language)

    result = AdoptResult(is_git_repo=is_git_repo, safety_report=report)

    for writer in (
        write_project_files,
        write_learning_module,
        write_tier_adr,
    ):
        w, p = writer(target, ctx, skip_existing=skip_existing)
        result.written.extend(w)
        result.preserved.extend(p)

    w, p = write_workshop_state(target, tier, ctx, skip_existing=skip_existing)
    result.written.extend(w)
    result.preserved.extend(p)

    w, p = install_skills(target, skip_existing=skip_existing)
    result.written.extend(w)
    result.preserved.extend(p)

    if install_hooks:
        if is_git_repo:
            result.hooks_backup = backup_hooks(target)
            hw, hp = install_hooks_into(target, skip_existing=skip_existing)
            result.hooks_written = hw
            result.hooks_preserved = hp
        else:
            result.hooks_skipped = True

    manifest = Manifest(
        project_name=project_name,
        tier=tier,
        language=language,
        mode="adopt",
        managed_files=[str(p) for p in result.written],
        preserved_files=[str(p) for p in result.preserved],
        hooks_installed=[p.name for p in result.hooks_written],
        hooks_preserved=[p.name for p in result.hooks_preserved],
    )
    manifest_path = write_manifest(target, manifest)
    result.written.append(manifest_path.relative_to(target))

    return result


def _all_errors_overridden(report: PreAdoptReport, *, allow_dirty: bool) -> bool:
    """Return True iff every error in the report has a matching override flag set.

    Currently the only blocking error is the dirty-tree check, overridden by
    `allow_dirty`. As new error types are added, this function expands.
    """
    for err in report.errors:
        if "working tree is dirty" in err:
            if not allow_dirty:
                return False
        else:
            return False  # unknown error type — never auto-override
    return True


def language_at_adopt(target: Path, lang_flag: str | None) -> Language:
    """Resolve the language for adoption: explicit flag wins, else auto-detect."""
    if lang_flag:
        if lang_flag not in ("python", "typescript", "polyglot"):
            raise ValueError(f"Invalid language: {lang_flag!r}")
        return lang_flag  # type: ignore[return-value]
    detected = detect_language(target)
    if detected is None:
        return "polyglot"  # safe default for adopt — let runtime hooks figure it out
    return detected

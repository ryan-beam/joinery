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


class AlreadyAdoptedError(RuntimeError):
    """Raised when adopting a target that already has .workshop/tier.lock."""


def adopt(
    target: Path,
    *,
    tier: str,
    language: str,
    force: bool = False,
    install_hooks: bool = True,
) -> AdoptResult:
    """Overlay Joinery onto an existing codebase at `target`.

    Args:
        target: Existing directory to adopt. Must exist and be non-empty.
        tier: One of "production", "standard", "sketch".
        language: One of "python", "typescript", "polyglot".
        force: If True, overwrite existing files. Default: preserve them.
        install_hooks: If True (default) and target is a git repo, install
            framework hooks. Existing hooks are preserved unless force=True.

    Returns:
        AdoptResult summarizing what was written, preserved, and skipped.

    Raises:
        FileNotFoundError: target does not exist.
        ValueError: target exists but is empty (use `init` instead).
        AlreadyAdoptedError: target already has .workshop/tier.lock and
            force is False.
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

    project_name = target.resolve().name
    ctx = render_context(project_name=project_name, tier=tier, language=language)

    result = AdoptResult(is_git_repo=is_git_repo)

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
            hw, hp = install_hooks_into(target, skip_existing=skip_existing)
            result.hooks_written = hw
            result.hooks_preserved = hp
        else:
            result.hooks_skipped = True

    return result


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

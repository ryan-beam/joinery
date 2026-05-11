"""Pre-adopt safety scan.

Runs before `workshop adopt` writes anything. Inspects the target repo for
conditions that make adoption risky:

- **Dirty working tree** (ERROR — refuse adoption unless --allow-dirty)
- **Sensitive paths present** like .env, *.pem, credentials.json (WARN)
- **Existing git hooks** that adoption would chain alongside (INFO — backed up)
- **Other hook managers** like husky, lefthook, pre-commit framework (WARN)

The scan never modifies the project. It produces a `PreAdoptReport`; the
caller decides what to do with it (halt, warn, or proceed). Hook backup is
a separate function called by `adopt()` after the scan passes, not by the
scan itself.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from joinery import git

SENSITIVE_PATH_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
)

SENSITIVE_GLOB_PATTERNS: tuple[str, ...] = (
    "*.pem",
    "*.key",
    "*.pfx",
    "*.p12",
)

SENSITIVE_DIRECTORIES: tuple[str, ...] = (
    "secrets",
    ".aws",
    ".ssh",
    ".gnupg",
)

HOOK_MANAGER_INDICATORS: tuple[tuple[str, str], ...] = (
    (".husky", "husky"),
    ("lefthook.yml", "lefthook"),
    ("lefthook.yaml", "lefthook"),
    (".pre-commit-config.yaml", "pre-commit framework"),
    (".pre-commit-config.yml", "pre-commit framework"),
)


@dataclass
class PreAdoptReport:
    """Outcome of a pre-adopt scan.

    Errors halt adoption (unless overridden by a CLI flag). Warnings are
    surfaced but adoption proceeds. Info entries are noted without warning.
    """

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_findings(self) -> bool:
        return bool(self.errors or self.warnings or self.info)


class UnsafeAdoptError(RuntimeError):
    """Raised when the pre-adopt scan finds blocking errors and overrides are off."""

    def __init__(self, report: PreAdoptReport) -> None:
        super().__init__("Pre-adopt safety scan found blocking issues.")
        self.report = report


def scan(target: Path, *, install_hooks: bool = True) -> PreAdoptReport:
    """Run all safety checks against `target`. Returns the combined report."""
    report = PreAdoptReport()
    _check_git_clean(target, report)
    _check_sensitive_paths(target, report)
    _check_hook_managers(target, report)
    if install_hooks:
        _check_existing_hooks(target, report)
    return report


def backup_hooks(target: Path) -> Path | None:
    """Copy any existing non-sample hooks into `.joinery/backup/hooks-<timestamp>/`.

    Returns the backup directory path, or None if there were no hooks to back
    up (or `.git/hooks/` does not exist). Always non-destructive; only ever
    creates files.
    """
    hooks_dir = target / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return None
    existing = [p for p in hooks_dir.iterdir() if p.is_file() and not p.name.endswith(".sample")]
    if not existing:
        return None
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = target / ".joinery" / "backup" / f"hooks-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for hook in existing:
        shutil.copy2(hook, backup_dir / hook.name)
    return backup_dir


def _check_git_clean(target: Path, report: PreAdoptReport) -> None:
    """Adopt should run against a clean working tree so the diff is reviewable."""
    if not (target / ".git").is_dir():
        return  # not a git repo — git.is_clean would fail; handled elsewhere
    try:
        if not git.is_clean(target):
            report.errors.append(
                "working tree is dirty — commit or stash existing changes first, "
                "or pass --allow-dirty to proceed anyway"
            )
    except git.GitError as exc:
        report.warnings.append(f"could not check git status: {exc}")


def _check_sensitive_paths(target: Path, report: PreAdoptReport) -> None:
    """Surface sensitive files/directories Joinery might inadvertently touch."""
    found: list[str] = []
    for name in SENSITIVE_PATH_PATTERNS:
        if (target / name).exists():
            found.append(name)
    for pattern in SENSITIVE_GLOB_PATTERNS:
        for match in target.glob(pattern):
            if match.is_file():
                found.append(match.relative_to(target).as_posix())
    for dir_name in SENSITIVE_DIRECTORIES:
        if (target / dir_name).is_dir():
            found.append(f"{dir_name}/")
    if not found:
        return
    items = ", ".join(sorted(set(found)))
    report.warnings.append(
        f"sensitive paths present: {items}. Verify they are in .gitignore "
        f"and that Joinery's hooks won't accidentally commit them."
    )


def _check_existing_hooks(target: Path, report: PreAdoptReport) -> None:
    """List non-sample hooks already in `.git/hooks/`. They'll be backed up."""
    hooks_dir = target / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return
    existing = [
        p.name for p in hooks_dir.iterdir() if p.is_file() and not p.name.endswith(".sample")
    ]
    if not existing:
        return
    listed = ", ".join(sorted(existing))
    report.info.append(f"existing git hooks will be backed up before install: {listed}")


def _check_hook_managers(target: Path, report: PreAdoptReport) -> None:
    """Detect alternative hook managers that may conflict with Joinery's hooks."""
    detected: list[str] = []
    for path, label in HOOK_MANAGER_INDICATORS:
        if (target / path).exists():
            detected.append(label)
    if not detected:
        return
    unique = sorted(set(detected))
    label_list = ", ".join(unique)
    report.warnings.append(
        f"alternative hook manager(s) detected: {label_list}. Joinery's hooks "
        f"may chain awkwardly. Review .git/hooks/ after adoption to confirm "
        f"the order is sensible."
    )

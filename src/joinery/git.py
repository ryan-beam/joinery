"""Git helpers — thin wrappers around git subprocess calls.

The workshop CLI uses git to: init repos, install hooks, commit scaffolded
state, query branch/status. Each function is a deliberate boundary so the
rest of the codebase doesn't sprinkle subprocess calls everywhere.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git subprocess call fails."""


def _run(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command and return stdout. Raise GitError with stderr on failure."""
    # S603/S607: We invoke `git` from PATH with controlled args. The framework
    # depends on a working git installation; resolving the full path here would
    # add complexity without security benefit (PATH manipulation is already a
    # broader concern than this call).
    result = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def init_repo(cwd: Path, initial_branch: str = "main") -> None:
    """Initialize a git repo at cwd with the given initial branch."""
    _run(["init", "-b", initial_branch], cwd=cwd)


def install_hook(hook_source: Path, project_root: Path) -> None:
    """Copy a hook script into .git/hooks/ and mark executable.

    Hooks are git-native (no `.sh` extension). Source file's basename becomes
    the hook name (e.g., hooks/pre-commit -> .git/hooks/pre-commit).
    """
    hook_target = project_root / ".git" / "hooks" / hook_source.name
    hook_target.parent.mkdir(parents=True, exist_ok=True)
    hook_target.write_bytes(hook_source.read_bytes())
    # chmod 0o755 — executable on Unix; harmless on Windows.
    hook_target.chmod(0o755)


def add_all(cwd: Path) -> None:
    _run(["add", "."], cwd=cwd)


def commit(cwd: Path, message: str, allow_empty: bool = False) -> str:
    """Create a commit. Returns the commit hash."""
    args = ["commit", "-m", message]
    if allow_empty:
        args.append("--allow-empty")
    _run(args, cwd=cwd)
    return _run(["rev-parse", "HEAD"], cwd=cwd).strip()


def current_branch(cwd: Path) -> str:
    return _run(["branch", "--show-current"], cwd=cwd).strip()


def status_short(cwd: Path) -> str:
    return _run(["status", "--short"], cwd=cwd)


def is_clean(cwd: Path) -> bool:
    return status_short(cwd).strip() == ""

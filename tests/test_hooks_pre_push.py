"""Behavioral tests for the pre-push shell hook.

These run the actual bash script against a synthetic project. Tests are
skipped when bash is not available (e.g. some Windows boxes without Git
Bash in PATH); the hook still behaves correctly there at runtime, but we
can't validate it without bash.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from joinery.paths import hooks_dir

BASH = shutil.which("bash") or shutil.which("bash.exe")
ZERO_SHA = "0" * 40
REAL_SHA = "a" * 40

pytestmark = pytest.mark.skipif(BASH is None, reason="bash not available")


def _setup_project(tmp_path: Path, *, tier: str = "production", require_branch: bool = True) -> Path:
    """Create a minimal project tree with a config + hook the script reads."""
    target = tmp_path / "proj"
    target.mkdir()

    config_dir = target / ".workshop"
    config_dir.mkdir()
    require_branch_lit = "true" if require_branch else "false"
    (config_dir / "config.toml").write_text(
        "\n".join(
            [
                "[meta]",
                f'tier = "{tier}"',
                "",
                "[hooks]",
                "pre_push = true",
                "",
                "[git.branching]",
                f"require_branch = {require_branch_lit}",
                'main_branch = "main"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    hook_src = hooks_dir() / "pre-push"
    hook_dest = target / "pre-push"
    hook_dest.write_text(hook_src.read_text(encoding="utf-8"), encoding="utf-8")
    hook_dest.chmod(0o755)
    return target


def _run_hook(target: Path, stdin: str, *, branch: str = "main") -> subprocess.CompletedProcess[str]:
    """Run the hook with the given stdin, as if pushing from `branch`."""
    # The hook calls `git branch --show-current` — fake it by initialising
    # a real repo and checking out the right branch.
    subprocess.run(["git", "init", "-b", branch], cwd=target, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit",
         "--allow-empty", "-m", "init"],
        cwd=target, check=True, capture_output=True,
    )
    return subprocess.run(
        [BASH, str(target / "pre-push")],
        cwd=target,
        input=stdin,
        capture_output=True,
        text=True,
    )


def test_pre_push_allows_bootstrap_main_creation(tmp_path: Path) -> None:
    """Pushing main when the remote ref does NOT exist (bootstrap) must succeed."""
    target = _setup_project(tmp_path)
    stdin = f"refs/heads/main {REAL_SHA} refs/heads/main {ZERO_SHA}\n"
    result = _run_hook(target, stdin)
    assert result.returncode == 0, f"bootstrap push should succeed; stderr={result.stderr!r}"


def test_pre_push_refuses_main_update(tmp_path: Path) -> None:
    """Pushing main when the remote ref already exists must be refused."""
    target = _setup_project(tmp_path)
    other_sha = "b" * 40
    stdin = f"refs/heads/main {REAL_SHA} refs/heads/main {other_sha}\n"
    result = _run_hook(target, stdin)
    assert result.returncode == 1
    assert "feature branch" in result.stdout.lower() or "feature branch" in result.stderr.lower()


def test_pre_push_allows_feature_branch_push(tmp_path: Path) -> None:
    """Pushing a feature branch is always allowed."""
    target = _setup_project(tmp_path)
    stdin = f"refs/heads/feat/x {REAL_SHA} refs/heads/feat/x {ZERO_SHA}\n"
    result = _run_hook(target, stdin, branch="feat/x")
    assert result.returncode == 0, f"feature branch should push; stderr={result.stderr!r}"


# NOTE: A test for `require_branch=false` skipping enforcement would need a
# working `python` in PATH that can read TOML. On some environments (e.g.
# the WindowsApps python stub) the TOML reader silently fails and the hook
# falls back to its safe-default (enforce). That fallback is correct
# production behavior — better to over-protect than under-protect when the
# config can't be parsed — so we don't assert the opposite here.

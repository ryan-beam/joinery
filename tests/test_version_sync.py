"""Tests for the version-sync invariant + bump helper.

CLAUDE.md rule #6: pyproject.toml and src/joinery/__init__.py must agree.
The May 19, 2026 scar (PRs #21/#22/#23 bumped pyproject only, three silent
releases drifted) led to:

  - scripts/bump_version.py — atomic helper
  - scripts/check_version_sync.py — pre-commit guard
  - this test file — locks the invariant under CI as well

Tests run the scripts as subprocesses against a temporary copy of the repo
layout so the real version files aren't mutated.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUMP_SCRIPT = REPO_ROOT / "scripts" / "bump_version.py"
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check_version_sync.py"


def _seed_repo(tmp: Path, pyproject_v: str, init_v: str) -> None:
    """Build a minimal repo layout matching what the scripts expect."""
    (tmp / "src" / "joinery").mkdir(parents=True)
    (tmp / "scripts").mkdir()
    (tmp / "pyproject.toml").write_text(
        f'[project]\nname = "joinery-cli"\nversion = "{pyproject_v}"\n',
        encoding="utf-8",
    )
    (tmp / "src" / "joinery" / "__init__.py").write_text(
        f'"""docstring"""\n\n__version__ = "{init_v}"\n',
        encoding="utf-8",
    )
    shutil.copy(BUMP_SCRIPT, tmp / "scripts" / "bump_version.py")
    shutil.copy(CHECK_SCRIPT, tmp / "scripts" / "check_version_sync.py")


def _read_pyproject_version(repo: Path) -> str:
    import re

    text = (repo / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'version = "([^"]+)"', text).group(1)


def _read_init_version(repo: Path) -> str:
    import re

    text = (repo / "src" / "joinery" / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', text).group(1)


# ---------------------------------------------------------------------------
# check_version_sync.py
# ---------------------------------------------------------------------------


class TestCheckVersionSync:
    def test_passes_when_in_sync(self, tmp_path: Path) -> None:
        _seed_repo(tmp_path, "0.1.15", "0.1.15")
        result = subprocess.run(
            [sys.executable, "scripts/check_version_sync.py"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"expected pass, got stderr: {result.stderr}"

    def test_fails_when_drift(self, tmp_path: Path) -> None:
        _seed_repo(tmp_path, "0.1.15", "0.1.12")
        result = subprocess.run(
            [sys.executable, "scripts/check_version_sync.py"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "version drift detected" in result.stderr
        assert "0.1.15" in result.stderr
        assert "0.1.12" in result.stderr
        assert "rule #6" in result.stderr.lower()


# ---------------------------------------------------------------------------
# bump_version.py
# ---------------------------------------------------------------------------


class TestBumpVersion:
    def test_bumps_both_files_atomically(self, tmp_path: Path) -> None:
        _seed_repo(tmp_path, "0.1.15", "0.1.15")
        result = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "0.1.16"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"expected success, got: {result.stderr}"
        assert _read_pyproject_version(tmp_path) == "0.1.16"
        assert _read_init_version(tmp_path) == "0.1.16"

    def test_refuses_when_files_already_disagree(self, tmp_path: Path) -> None:
        """If the two files already drift, bump_version refuses rather than
        burying the drift in a new value."""
        _seed_repo(tmp_path, "0.1.15", "0.1.12")
        result = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "0.1.20"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "already disagree" in result.stderr
        # Files unchanged
        assert _read_pyproject_version(tmp_path) == "0.1.15"
        assert _read_init_version(tmp_path) == "0.1.12"

    def test_rejects_invalid_semver(self, tmp_path: Path) -> None:
        _seed_repo(tmp_path, "0.1.15", "0.1.15")
        for bad in ("1.2", "v1", "abc", "1.2.3.4.5", ""):
            result = subprocess.run(
                [sys.executable, "scripts/bump_version.py", bad],
                cwd=tmp_path,
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0, f"expected reject for {bad!r}"

    def test_accepts_semver_with_v_prefix(self, tmp_path: Path) -> None:
        """Common ergonomic: allow `v0.1.16` and `0.1.16` both."""
        _seed_repo(tmp_path, "0.1.15", "0.1.15")
        result = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "v0.1.16"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert _read_pyproject_version(tmp_path) == "0.1.16"
        assert _read_init_version(tmp_path) == "0.1.16"

    def test_noop_when_already_at_target(self, tmp_path: Path) -> None:
        _seed_repo(tmp_path, "0.1.16", "0.1.16")
        result = subprocess.run(
            [sys.executable, "scripts/bump_version.py", "0.1.16"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "no change" in result.stdout


# ---------------------------------------------------------------------------
# Live repo invariant — guards against drift in the actual joinery checkout
# ---------------------------------------------------------------------------


def test_live_repo_versions_in_sync() -> None:
    """The actual joinery repo's two version sources must always match.
    If this fails: someone bumped one file without the other. Run
    `python scripts/bump_version.py <X.Y.Z>` to fix.
    """
    py = _read_pyproject_version(REPO_ROOT)
    init = _read_init_version(REPO_ROOT)
    assert py == init, (
        f"version drift: pyproject.toml={py} but src/joinery/__init__.py={init}. "
        "See CLAUDE.md rule #6."
    )

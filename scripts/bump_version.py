#!/usr/bin/env python3
"""Atomic version bump for Joinery.

Joinery has TWO version sources that MUST stay in sync:
  1. `pyproject.toml`              — read by pip / `pip show joinery-cli`
  2. `src/joinery/__init__.py`     — read by the `workshop` CLI (`workshop --version`)

The May 19, 2026 incident: PRs #21/#22/#23 bumped `pyproject.toml` only. `workshop
--version` kept reporting 0.1.12 while pip thought it was 0.1.15. Three releases
silently drifted. CLAUDE.md rule #6 codifies the failure; this script enforces it.

Usage:
    python scripts/bump_version.py 0.1.16

The script reads both files, asserts they agree on the OLD version, writes the
new version to both, then prints a summary. Refuses to run if the two files
already disagree (forces a manual reconciliation rather than burying the drift).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
INIT_FILE = REPO_ROOT / "src" / "joinery" / "__init__.py"

PYPROJECT_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"$', re.MULTILINE)
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"$', re.MULTILINE)
VERSION_FORMAT_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][\w.]+)?$")


def read_pyproject_version() -> str:
    m = PYPROJECT_VERSION_RE.search(PYPROJECT.read_text(encoding="utf-8"))
    if not m:
        raise RuntimeError(f"No version found in {PYPROJECT}")
    return m.group(1)


def read_init_version() -> str:
    m = INIT_VERSION_RE.search(INIT_FILE.read_text(encoding="utf-8"))
    if not m:
        raise RuntimeError(f"No __version__ found in {INIT_FILE}")
    return m.group(1)


def write_pyproject_version(new_version: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text = PYPROJECT_VERSION_RE.sub(f'version = "{new_version}"', text, count=1)
    if text == new_text:
        raise RuntimeError(f"Failed to replace version in {PYPROJECT}")
    PYPROJECT.write_text(new_text, encoding="utf-8")


def write_init_version(new_version: str) -> None:
    text = INIT_FILE.read_text(encoding="utf-8")
    new_text = INIT_VERSION_RE.sub(f'__version__ = "{new_version}"', text, count=1)
    if text == new_text:
        raise RuntimeError(f"Failed to replace __version__ in {INIT_FILE}")
    INIT_FILE.write_text(new_text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    new_version = sys.argv[1].lstrip("v")
    if not VERSION_FORMAT_RE.match(new_version):
        print(
            f"error: '{new_version}' is not a SemVer string (expected X.Y.Z or X.Y.Z-suffix)",
            file=sys.stderr,
        )
        return 2

    pyproject_v = read_pyproject_version()
    init_v = read_init_version()

    if pyproject_v != init_v:
        print(
            "error: version sources already disagree — "
            f"pyproject.toml={pyproject_v} vs __init__.py={init_v}.\n"
            "Reconcile manually before bumping. The pre-commit hook should have caught "
            "this; if you're seeing it here, the hook was bypassed or absent.",
            file=sys.stderr,
        )
        return 1

    if new_version == pyproject_v:
        print(f"no change: both files already at {new_version}")
        return 0

    write_pyproject_version(new_version)
    write_init_version(new_version)

    print(f"bumped {pyproject_v} -> {new_version}")
    print(f"  {PYPROJECT.relative_to(REPO_ROOT)}")
    print(f"  {INIT_FILE.relative_to(REPO_ROOT)}")
    print()
    print("next steps:")
    print("  pip install -e . --quiet    # refresh the CLI install")
    print(f"  workshop --version          # should report {new_version}")
    print("  # then commit both files with the changelog entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())

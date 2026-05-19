#!/usr/bin/env python3
"""Pre-commit guard: pyproject.toml and src/joinery/__init__.py must agree on version.

Exits 0 if the two files report the same version, non-zero with a diagnostic
otherwise. Wired into `hooks/pre-commit`. Companion to `scripts/bump_version.py`
which updates both files atomically.

Rationale: CLAUDE.md rule #6 (May 19, 2026 scar — PRs #21/#22/#23 bumped
pyproject only; workshop --version reported stale 0.1.12 while pip thought it
was 0.1.15). Three silent releases drifted.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
INIT_FILE = REPO_ROOT / "src" / "joinery" / "__init__.py"


def main() -> int:
    try:
        pyproject_text = PYPROJECT.read_text(encoding="utf-8")
        init_text = INIT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        print(f"version-sync check: cannot read {e.filename}", file=sys.stderr)
        return 1

    py_match = re.search(r'^version\s*=\s*"([^"]+)"$', pyproject_text, re.MULTILINE)
    init_match = re.search(r'^__version__\s*=\s*"([^"]+)"$', init_text, re.MULTILINE)

    if not py_match:
        print(f"version-sync check: no version in {PYPROJECT.name}", file=sys.stderr)
        return 1
    if not init_match:
        print(f"version-sync check: no __version__ in {INIT_FILE.name}", file=sys.stderr)
        return 1

    py_ver = py_match.group(1)
    init_ver = init_match.group(1)

    if py_ver != init_ver:
        print(
            "pre-commit failed: version drift detected.\n"
            f"  pyproject.toml = {py_ver}\n"
            f"  __init__.py    = {init_ver}\n"
            "Use `python scripts/bump_version.py <X.Y.Z>` to bump atomically.\n"
            "See CLAUDE.md rule #6.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

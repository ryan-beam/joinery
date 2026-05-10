"""Language detection for projects scaffolded by `workshop init`.

Language is a HINT, not a lock. The framework adapts to whatever the project
contains at runtime; this module only affects what gets scaffolded at init time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

Language = Literal["python", "typescript", "polyglot"]

SUPPORTED_LANGUAGES: tuple[Language, ...] = ("python", "typescript", "polyglot")


def detect_language(cwd: Path) -> Language | None:
    """Detect primary language from files present in the given directory.

    Returns None if neither Python nor TypeScript indicators are found,
    signaling that the caller should prompt the user.
    """
    has_python = (cwd / "pyproject.toml").is_file() or any(cwd.glob("*.py"))
    has_typescript = (cwd / "package.json").is_file() or (cwd / "tsconfig.json").is_file()

    if has_python and has_typescript:
        return "polyglot"
    if has_python:
        return "python"
    if has_typescript:
        return "typescript"
    return None


def is_supported(value: str) -> bool:
    return value in SUPPORTED_LANGUAGES

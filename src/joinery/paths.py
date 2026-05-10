"""Locate framework data directories (templates/, hooks/, skills/).

In an editable install, the data lives at the repo root next to src/.
In a wheel install, the data lives inside the package at joinery/_data/.
"""

from __future__ import annotations

from pathlib import Path


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _repo_root_candidate() -> Path:
    # src/joinery/__file__ -> repo_root/src/joinery/paths.py
    # Two parents up = repo_root.
    return _package_root().parent.parent


def find_data_dir(name: str) -> Path:
    """Return the path to a framework data directory.

    Args:
        name: One of "templates", "hooks", "skills".

    Raises:
        FileNotFoundError: If the directory cannot be located.
    """
    bundled = _package_root() / "_data" / name
    if bundled.is_dir():
        return bundled
    repo_root_dir = _repo_root_candidate() / name
    if repo_root_dir.is_dir():
        return repo_root_dir
    raise FileNotFoundError(
        f"Could not locate '{name}/' directory. Looked at: {bundled} and {repo_root_dir}"
    )


def templates_dir() -> Path:
    return find_data_dir("templates")


def hooks_dir() -> Path:
    return find_data_dir("hooks")


def skills_dir() -> Path:
    return find_data_dir("skills")

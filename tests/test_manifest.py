"""Tests for joinery.manifest — the .workshop/answers.toml file."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from joinery.manifest import (
    ANSWER_FILE_RELPATH,
    Manifest,
    read_manifest,
    write_manifest,
)


def test_write_manifest_creates_answer_file(tmp_path: Path) -> None:
    manifest = Manifest(
        project_name="hello",
        tier="production",
        language="python",
        mode="init",
        managed_files=["CLAUDE.md", "plan.md"],
        hooks_installed=["pre-commit"],
    )
    path = write_manifest(tmp_path, manifest)
    assert path == tmp_path / ANSWER_FILE_RELPATH
    assert path.is_file()


def test_write_manifest_fills_created_at(tmp_path: Path) -> None:
    manifest = Manifest(project_name="x", tier="standard", language="python", mode="init")
    write_manifest(tmp_path, manifest)
    assert manifest.created_at  # filled in by write_manifest
    # ISO 8601 UTC: contains 'T' and ends with '+00:00'
    assert "T" in manifest.created_at
    assert manifest.created_at.endswith("+00:00")


def test_read_manifest_returns_none_when_absent(tmp_path: Path) -> None:
    assert read_manifest(tmp_path) is None


def test_round_trip_preserves_fields(tmp_path: Path) -> None:
    original = Manifest(
        project_name="round-trip",
        tier="sketch",
        language="typescript",
        mode="adopt",
        managed_files=["CLAUDE.md", "plan.md", ".workshop/config.toml"],
        preserved_files=["README.md", "AGENTS.md"],
        hooks_installed=["pre-commit", "pre-push"],
        hooks_preserved=["commit-msg"],
    )
    write_manifest(tmp_path, original)
    loaded = read_manifest(tmp_path)
    assert loaded is not None
    assert loaded.project_name == "round-trip"
    assert loaded.tier == "sketch"
    assert loaded.language == "typescript"
    assert loaded.mode == "adopt"
    assert loaded.managed_files == sorted(original.managed_files)
    assert loaded.preserved_files == sorted(original.preserved_files)
    assert loaded.hooks_installed == sorted(original.hooks_installed)
    assert loaded.hooks_preserved == sorted(original.hooks_preserved)
    assert loaded.created_at == original.created_at


def test_serialized_file_is_valid_toml(tmp_path: Path) -> None:
    manifest = Manifest(
        project_name="toml-check",
        tier="production",
        language="python",
        mode="init",
        managed_files=["CLAUDE.md"],
    )
    path = write_manifest(tmp_path, manifest)
    with path.open("rb") as f:
        parsed = tomllib.load(f)
    assert parsed["project_name"] == "toml-check"
    assert parsed["mode"] == "init"
    assert parsed["files"]["managed"] == ["CLAUDE.md"]


def test_read_manifest_rejects_invalid_mode(tmp_path: Path) -> None:
    path = tmp_path / ANSWER_FILE_RELPATH
    path.parent.mkdir(parents=True)
    path.write_text(
        'joinery_version = "0.1.2"\n'
        'mode = "destroy"\n'
        'tier = "production"\n'
        'language = "python"\n'
        'project_name = "x"\n'
        'created_at = "2026-05-11T00:00:00+00:00"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid mode"):
        read_manifest(tmp_path)


def test_serializer_escapes_quotes_in_project_name(tmp_path: Path) -> None:
    """A project name containing quotes must round-trip safely."""
    manifest = Manifest(
        project_name='weird "name"',
        tier="standard",
        language="python",
        mode="init",
    )
    write_manifest(tmp_path, manifest)
    loaded = read_manifest(tmp_path)
    assert loaded is not None
    assert loaded.project_name == 'weird "name"'


def test_empty_lists_serialize_as_inline_empty(tmp_path: Path) -> None:
    manifest = Manifest(project_name="x", tier="sketch", language="python", mode="init")
    path = write_manifest(tmp_path, manifest)
    text = path.read_text(encoding="utf-8")
    assert "managed = []" in text
    assert "preserved = []" in text
    assert "installed = []" in text

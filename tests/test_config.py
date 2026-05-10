"""Tests for joinery.config — TOML read helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from joinery.config import get_primary_language, get_tier, read_config


def _write_minimal_config(
    project_root: Path, tier: str = "standard", language: str = "python"
) -> None:
    workshop_dir = project_root / ".workshop"
    workshop_dir.mkdir()
    (workshop_dir / "config.toml").write_text(
        f"""
[meta]
project_name = "test"
tier = "{tier}"

[lang]
primary = "{language}"
""",
        encoding="utf-8",
    )


def test_read_config_returns_dict(tmp_path: Path) -> None:
    _write_minimal_config(tmp_path)
    config = read_config(tmp_path)
    assert config["meta"]["project_name"] == "test"


def test_read_config_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not a Joinery project"):
        read_config(tmp_path)


def test_get_tier_returns_value(tmp_path: Path) -> None:
    _write_minimal_config(tmp_path, tier="production")
    assert get_tier(read_config(tmp_path)) == "production"


def test_get_tier_defaults_to_standard_when_missing() -> None:
    assert get_tier({}) == "standard"


def test_get_tier_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid tier"):
        get_tier({"meta": {"tier": "platinum"}})


def test_get_primary_language(tmp_path: Path) -> None:
    _write_minimal_config(tmp_path, language="typescript")
    assert get_primary_language(read_config(tmp_path)) == "typescript"


def test_get_primary_language_defaults_to_python() -> None:
    assert get_primary_language({}) == "python"

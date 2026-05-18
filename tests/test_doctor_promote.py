"""Tests for joinery.doctor and joinery.promote."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from joinery.cli import main
from joinery.init import scaffold


def test_doctor_on_non_joinery_project(tmp_path: Path) -> None:
    """Doctor reports missing config and exits cleanly on non-Joinery projects."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert "Not a Joinery project" in result.output


def test_doctor_on_scaffolded_project(tmp_path: Path) -> None:
    """Doctor reports valid config and tier on a freshly scaffolded project."""
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    runner = CliRunner()
    result = runner.invoke(main, ["doctor", "--project", str(target)])
    assert result.exit_code == 0
    assert "valid (tier=standard)" in result.output


def test_promote_refuses_demotion(tmp_path: Path) -> None:
    """Promoting from production to standard should fail (demotion not supported)."""
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="production", language="python", init_git=True)
    runner = CliRunner()
    result = runner.invoke(main, ["promote", str(target), "--to", "standard"])
    assert result.exit_code != 0
    assert "Cannot promote" in result.output


def test_promote_sketch_to_standard(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="sketch", language="python", init_git=True)
    runner = CliRunner()
    result = runner.invoke(main, ["promote", str(target), "--to", "standard"])
    assert result.exit_code == 0, result.output
    config = (target / ".workshop" / "config.toml").read_text(encoding="utf-8")
    assert 'tier = "standard"' in config


@pytest.mark.parametrize(
    "source_tier,target_tier",
    [
        ("sketch", "standard"),
        ("sketch", "production"),
        ("standard", "production"),
    ],
)
def test_promote_paths(tmp_path: Path, source_tier: str, target_tier: str) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier=source_tier, language="python", init_git=True)
    runner = CliRunner()
    result = runner.invoke(main, ["promote", str(target), "--to", target_tier])
    assert result.exit_code == 0, result.output


def test_cli_version() -> None:
    """Version output must reflect the actual package version, not be hardcoded."""
    from joinery import __version__

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "session" in result.output
    assert "promote" in result.output
    assert "doctor" in result.output

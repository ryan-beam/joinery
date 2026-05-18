"""Tests for joinery.init — scaffolding a new project.

Covers the matrix of tier x language permutations. The init function should
produce the expected directory tree, render templates with correct placeholders,
and (when init_git=True) commit the initial state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from joinery.init import scaffold
from joinery.manifest import read_manifest


@pytest.mark.parametrize("tier", ["production", "standard", "sketch"])
@pytest.mark.parametrize("language", ["python", "typescript", "polyglot"])
def test_scaffold_produces_expected_files(tmp_path: Path, tier: str, language: str) -> None:
    """9 init paths (3 tiers x 3 lang modes) all produce a valid scaffold."""
    target = tmp_path / "my-project"
    written = scaffold(
        target=target,
        project_name="my-project",
        tier=tier,
        language=language,
        init_git=False,
    )
    assert (target / "CLAUDE.md").is_file()
    assert (target / "plan.md").is_file()
    assert (target / "HANDOVER.md").is_file()
    assert (target / "README.md").is_file()
    assert (target / "AGENTS.md").is_file()
    assert (target / ".workshop" / "config.toml").is_file()
    assert (target / ".workshop" / "tier.lock").is_file()
    assert (target / "docs" / "decisions" / "0001-tier-selection.md").is_file()
    assert len(written) > 0


def test_scaffold_writes_tier_into_config(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="production", language="python", init_git=False)
    config_text = (target / ".workshop" / "config.toml").read_text(encoding="utf-8")
    assert 'tier = "production"' in config_text


def test_scaffold_writes_project_name_into_files(tmp_path: Path) -> None:
    target = tmp_path / "cool-app"
    scaffold(
        target=target, project_name="cool-app", tier="standard", language="python", init_git=False
    )
    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "cool-app" in claude_text


def test_scaffold_refuses_non_empty_directory(tmp_path: Path) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "file.txt").write_text("hi", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists and is not empty"):
        scaffold(
            target=target, project_name="x", tier="standard", language="python", init_git=False
        )


def test_scaffold_writes_tier_lock(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="sketch", language="python", init_git=False)
    assert (target / ".workshop" / "tier.lock").read_text(encoding="utf-8").strip() == "sketch"


def test_scaffold_with_git_creates_repo(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=True)
    assert (target / ".git").is_dir()


def test_scaffold_path_with_spaces(tmp_path: Path) -> None:
    """Cross-platform: paths with spaces should work."""
    target = tmp_path / "project with spaces"
    scaffold(
        target=target,
        project_name="project-with-spaces",
        tier="standard",
        language="python",
        init_git=False,
    )
    assert (target / "CLAUDE.md").is_file()


def test_scaffold_writes_answer_file(tmp_path: Path) -> None:
    """init must write .workshop/answers.toml recording managed state."""
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="production", language="python", init_git=False)
    manifest = read_manifest(target)
    assert manifest is not None
    assert manifest.mode == "init"
    assert manifest.tier == "production"
    assert manifest.language == "python"
    assert manifest.project_name == "p"
    assert "CLAUDE.md" in manifest.managed_files
    assert "plan.md" in manifest.managed_files
    assert manifest.preserved_files == []  # nothing preserved on greenfield init


def test_scaffold_with_git_records_hooks_in_manifest(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=True)
    manifest = read_manifest(target)
    assert manifest is not None
    assert "pre-commit" in manifest.hooks_installed
    assert "pre-push" in manifest.hooks_installed


def test_scaffold_writes_managed_by_marker_in_claude(tmp_path: Path) -> None:
    """CLAUDE.md should carry the managed-by sentinel for future update detection."""
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<!-- managed-by: joinery@" in claude_text


def test_scaffold_dry_run_does_not_touch_filesystem(tmp_path: Path) -> None:
    target = tmp_path / "p"
    written = scaffold(
        target=target,
        project_name="p",
        tier="production",
        language="python",
        init_git=False,
        dry_run=True,
    )
    assert not target.exists()
    # But the return value reports what would have been written.
    assert any(p == Path("CLAUDE.md") for p in written)


def test_scaffold_real_run_writes_transaction_log(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    txn_dir = target / ".joinery" / "transactions"
    assert txn_dir.is_dir()
    assert len(list(txn_dir.glob("*.json"))) == 1


@pytest.mark.parametrize("language", ["python", "typescript", "polyglot"])
def test_scaffold_writes_gitignore(tmp_path: Path, language: str) -> None:
    """Every init must scaffold a .gitignore appropriate for the language."""
    target = tmp_path / "p"
    scaffold(
        target=target, project_name="p", tier="production", language=language, init_git=False
    )
    gi = target / ".gitignore"
    assert gi.is_file(), f"missing .gitignore for language={language}"
    text = gi.read_text(encoding="utf-8")
    # Common entries every language scaffold must include.
    assert ".joinery/" in text, ".gitignore must hide .joinery/ audit state"
    assert ".workshop/usage.jsonl" in text, ".gitignore must hide local usage log"
    assert ".env" in text, ".gitignore must hide .env secrets"


def test_scaffold_gitignore_python_specific(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    text = (target / ".gitignore").read_text(encoding="utf-8")
    assert "__pycache__/" in text
    assert ".venv/" in text


def test_scaffold_gitignore_typescript_specific(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(
        target=target, project_name="p", tier="standard", language="typescript", init_git=False
    )
    text = (target / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in text


def test_scaffold_gitignore_in_manifest(tmp_path: Path) -> None:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    manifest = read_manifest(target)
    assert manifest is not None
    assert ".gitignore" in manifest.managed_files


def test_scaffold_installs_skills_to_both_locations(tmp_path: Path) -> None:
    """Skills must land in BOTH .claude/skills/ (user-global style) AND
    .claude/commands/ (Claude Code project-local slash commands) so users
    get auto-discovery + explicit /skill-name invocation both."""
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="production", language="python", init_git=False)

    skills_dir = target / ".claude" / "skills"
    commands_dir = target / ".claude" / "commands"

    assert skills_dir.is_dir()
    assert commands_dir.is_dir()

    # Both dirs should contain the same set of skill files (no README).
    skills_files = {p.name for p in skills_dir.glob("*.md")}
    commands_files = {p.name for p in commands_dir.glob("*.md")}
    assert skills_files == commands_files
    assert "mark.md" in skills_files
    assert "plan.md" in skills_files
    assert "sq.md" in skills_files
    assert "README.md" not in skills_files  # README is filtered out


def test_scaffold_version_string_matches_package(tmp_path: Path) -> None:
    """When the framework writes managed-by markers and answer files, the
    version must match the package version — never the stale 0.1.0 hardcode."""
    from joinery import __version__

    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert f"managed-by: joinery@{__version__}" in claude_text

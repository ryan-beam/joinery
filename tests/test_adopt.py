"""Tests for joinery.adopt — overlaying the framework onto existing codebases.

These exercise the contract of `adopt()`: non-destructive by default, opt-in
overwrite via force, refuses re-adoption, doesn't auto-commit, handles
non-git targets gracefully.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from joinery.adopt import AlreadyAdoptedError, adopt, language_at_adopt
from joinery.manifest import read_manifest
from joinery.preadopt import UnsafeAdoptError


def _make_existing_project(tmp_path: Path, *, with_git: bool = True, clean: bool = True) -> Path:
    """Create a minimal existing project to adopt into.

    By default the project is initialized with git AND has its initial files
    committed, so the working tree is clean. Pass `clean=False` to leave
    files uncommitted (used to test the dirty-tree safety check).
    """
    target = tmp_path / "existing-app"
    target.mkdir()
    (target / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (target / "README.md").write_text("# existing-app\n\nMy app.\n", encoding="utf-8")
    if with_git:
        subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
        if clean:
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@t",
                    "-c",
                    "user.name=t",
                    "add",
                    "-A",
                ],
                cwd=target,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=t@t",
                    "-c",
                    "user.name=t",
                    "commit",
                    "-m",
                    "initial",
                ],
                cwd=target,
                check=True,
                capture_output=True,
            )
    return target


def test_adopt_refuses_empty_directory(tmp_path: Path) -> None:
    """Adopt is for existing projects; greenfield should use init instead."""
    target = tmp_path / "empty"
    target.mkdir()
    with pytest.raises(ValueError, match="empty"):
        adopt(target, tier="standard", language="python")


def test_adopt_refuses_missing_directory(tmp_path: Path) -> None:
    target = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        adopt(target, tier="standard", language="python")


def test_adopt_writes_framework_files_into_existing_project(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    result = adopt(target, tier="production", language="python")
    assert (target / "CLAUDE.md").is_file()
    assert (target / "plan.md").is_file()
    assert (target / "AGENTS.md").is_file()
    assert (target / "HANDOVER.md").is_file()
    assert (target / ".workshop" / "config.toml").is_file()
    assert (target / ".workshop" / "tier.lock").is_file()
    assert len(result.written) > 0


def test_adopt_preserves_existing_readme_by_default(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    original_readme = (target / "README.md").read_text(encoding="utf-8")
    result = adopt(target, tier="standard", language="python")
    assert (target / "README.md").read_text(encoding="utf-8") == original_readme
    assert Path("README.md") in result.preserved


def test_adopt_force_overwrites_existing_files(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    original_readme = (target / "README.md").read_text(encoding="utf-8")
    adopt(target, tier="standard", language="python", force=True)
    # With force, README.md should now be the Joinery template, not the original
    new_readme = (target / "README.md").read_text(encoding="utf-8")
    assert new_readme != original_readme
    assert "existing-app" in new_readme  # template renders project_name


def test_adopt_refuses_reentry_without_force(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python")
    with pytest.raises(AlreadyAdoptedError, match="already adopted"):
        adopt(target, tier="standard", language="python")


def test_adopt_force_allows_reentry(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python")
    # After first adopt the working tree is dirty (new files); allow_dirty here
    # is intentional to focus the test on re-entry behavior, not the safety scan.
    result = adopt(target, tier="standard", language="python", force=True, allow_dirty=True)
    assert (target / ".workshop" / "tier.lock").read_text(encoding="utf-8").strip() == "standard"
    assert len(result.written) > 0


def test_adopt_installs_hooks_in_git_repo(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path, with_git=True)
    result = adopt(target, tier="production", language="python")
    assert (target / ".git" / "hooks" / "pre-commit").is_file()
    assert (target / ".git" / "hooks" / "pre-push").is_file()
    assert len(result.hooks_written) >= 1
    assert result.is_git_repo is True


def test_adopt_skips_hooks_on_non_git_target(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path, with_git=False)
    result = adopt(target, tier="standard", language="python")
    assert not (target / ".git").exists()
    assert result.is_git_repo is False
    assert result.hooks_skipped is True
    assert result.hooks_written == []


def test_adopt_no_hooks_flag_skips_hook_install(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path, with_git=True)
    result = adopt(target, tier="standard", language="python", install_hooks=False)
    assert not (target / ".git" / "hooks" / "pre-commit").exists()
    assert result.hooks_written == []


def test_adopt_does_not_create_commit(tmp_path: Path) -> None:
    """The adopt() function must not auto-commit; the user reviews the diff."""
    target = _make_existing_project(tmp_path, with_git=True)
    # Make an initial commit so HEAD exists, otherwise git log fails
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=target,
        check=True,
        capture_output=True,
    )
    head_before = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True, check=True
    ).stdout.strip()

    adopt(target, tier="production", language="python")

    head_after = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert head_before == head_after, "adopt() must not create commits"

    # And the new files should show up as unstaged changes
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=target, capture_output=True, text=True, check=True
    ).stdout
    assert "CLAUDE.md" in status
    assert ".workshop" in status


def test_adopt_writes_tier_into_config(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    adopt(target, tier="sketch", language="python")
    config_text = (target / ".workshop" / "config.toml").read_text(encoding="utf-8")
    assert 'tier = "sketch"' in config_text
    assert (target / ".workshop" / "tier.lock").read_text(encoding="utf-8").strip() == "sketch"


def test_adopt_uses_directory_name_as_project_name(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    # _make_existing_project names the dir "existing-app"
    adopt(target, tier="standard", language="python")
    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "existing-app" in claude_text


def test_language_at_adopt_uses_flag_when_provided(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    assert language_at_adopt(target, "typescript") == "typescript"


def test_language_at_adopt_auto_detects_python(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    # main.py is present from the fixture
    assert language_at_adopt(target, None) == "python"


def test_language_at_adopt_falls_back_to_polyglot_when_undetectable(tmp_path: Path) -> None:
    """When no language signal exists, adopt falls back to polyglot.

    This differs from init, which defaults to python — adopt's bias is to
    trust runtime detection rather than guess.
    """
    target = tmp_path / "no-lang-signal"
    target.mkdir()
    (target / "data.txt").write_text("just data", encoding="utf-8")
    assert language_at_adopt(target, None) == "polyglot"


def test_language_at_adopt_rejects_invalid_flag(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    with pytest.raises(ValueError, match="Invalid language"):
        language_at_adopt(target, "rust")


def test_adopt_refuses_dirty_working_tree(tmp_path: Path) -> None:
    """Pre-adopt scan blocks adoption when there are uncommitted changes."""
    target = _make_existing_project(tmp_path, clean=False)
    with pytest.raises(UnsafeAdoptError) as exc_info:
        adopt(target, tier="production", language="python")
    assert any("working tree is dirty" in e for e in exc_info.value.report.errors)


def test_adopt_allow_dirty_bypasses_safety_check(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path, clean=False)
    result = adopt(target, tier="production", language="python", allow_dirty=True)
    assert (target / "CLAUDE.md").is_file()
    assert any("working tree is dirty" in e for e in result.safety_report.errors)


def test_adopt_skip_scan_bypasses_everything(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path, clean=False)
    # Drop a sensitive file too — would normally warn, but skip_scan suppresses
    (target / ".env").write_text("SECRET=x\n", encoding="utf-8")
    result = adopt(target, tier="standard", language="python", skip_scan=True)
    assert (target / "CLAUDE.md").is_file()
    assert result.safety_report.errors == []
    assert result.safety_report.warnings == []


def test_adopt_backs_up_existing_hooks_before_install(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    pre_existing_hook = target / ".git" / "hooks" / "pre-commit"
    pre_existing_hook.write_text("#!/bin/sh\necho 'user hook'\n", encoding="utf-8")
    result = adopt(target, tier="production", language="python", allow_dirty=True)
    assert result.hooks_backup is not None
    assert (result.hooks_backup / "pre-commit").is_file()
    # Backed-up copy preserves the original content
    assert "user hook" in (result.hooks_backup / "pre-commit").read_text(encoding="utf-8")


def test_adopt_dry_run_does_not_write_any_files(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    result = adopt(target, tier="production", language="python", dry_run=True)
    assert not (target / "CLAUDE.md").exists()
    assert not (target / "plan.md").exists()
    assert not (target / ".workshop").exists()
    assert not (target / ".joinery").exists()
    # But the return value reflects what would have happened
    assert any(p == Path("CLAUDE.md") for p in result.written)
    assert result.dry_run is True


def test_adopt_dry_run_does_not_write_transaction_log(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python", dry_run=True)
    assert not (target / ".joinery" / "transactions").exists()


def test_adopt_real_run_writes_transaction_log(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python")
    txn_dir = target / ".joinery" / "transactions"
    assert txn_dir.is_dir()
    txns = list(txn_dir.glob("*.json"))
    assert len(txns) == 1


def test_adopt_safety_report_warns_about_env(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    (target / ".env").write_text("API_KEY=x\n", encoding="utf-8")
    result = adopt(target, tier="standard", language="python", allow_dirty=True)
    assert any("sensitive paths present" in w for w in result.safety_report.warnings)


def test_adopt_writes_answer_file_with_managed_and_preserved(tmp_path: Path) -> None:
    """adopt must record managed AND preserved files in .workshop/answers.toml."""
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python")
    manifest = read_manifest(target)
    assert manifest is not None
    assert manifest.mode == "adopt"
    assert manifest.tier == "production"
    assert manifest.project_name == "existing-app"
    # README.md is preserved (existed in fixture); CLAUDE.md is written
    assert "CLAUDE.md" in manifest.managed_files
    assert "README.md" in manifest.preserved_files


def test_adopt_force_reentry_overwrites_answer_file(tmp_path: Path) -> None:
    """A --force re-adopt should produce a fresh manifest reflecting new tier."""
    target = _make_existing_project(tmp_path)
    adopt(target, tier="production", language="python")
    first = read_manifest(target)
    assert first is not None
    assert first.tier == "production"

    # allow_dirty=True because the first adopt leaves untracked files.
    adopt(target, tier="standard", language="python", force=True, allow_dirty=True)
    second = read_manifest(target)
    assert second is not None
    assert second.tier == "standard"


def test_adopt_writes_managed_by_marker(tmp_path: Path) -> None:
    """Files written during adopt should carry the managed-by sentinel."""
    target = _make_existing_project(tmp_path)
    adopt(target, tier="standard", language="python")
    claude_text = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<!-- managed-by: joinery@" in claude_text


def test_adopt_with_existing_workshop_config_preserves_without_force(tmp_path: Path) -> None:
    """An existing .workshop/config.toml from a prior partial adoption should be preserved."""
    target = _make_existing_project(tmp_path)
    workshop = target / ".workshop"
    workshop.mkdir()
    (workshop / "config.toml").write_text("# custom user content\n", encoding="utf-8")
    # No tier.lock yet, so this isn't a full prior adoption. The new file is
    # untracked so the working tree is dirty — allow_dirty keeps the focus on
    # the partial-adoption preservation behavior.
    result = adopt(target, tier="standard", language="python", allow_dirty=True)
    assert (workshop / "config.toml").read_text(encoding="utf-8") == "# custom user content\n"
    assert Path(".workshop/config.toml") in result.preserved


def test_adopt_writes_gitignore_when_missing(tmp_path: Path) -> None:
    """If the target has no .gitignore, adopt drops one in."""
    target = _make_existing_project(tmp_path)
    result = adopt(target, tier="production", language="python")
    gi = target / ".gitignore"
    assert gi.is_file()
    assert ".joinery/" in gi.read_text(encoding="utf-8")
    assert Path(".gitignore") in result.written


def test_adopt_preserves_existing_gitignore(tmp_path: Path) -> None:
    """If the user already has a .gitignore, adopt leaves it alone (non-destructive default)."""
    target = _make_existing_project(tmp_path)
    custom = "# my custom rules\nsecret_thing/\n"
    (target / ".gitignore").write_text(custom, encoding="utf-8")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", ".gitignore"],
        cwd=target,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-m",
            "add gitignore",
        ],
        cwd=target,
        check=True,
        capture_output=True,
    )
    result = adopt(target, tier="production", language="python")
    assert (target / ".gitignore").read_text(encoding="utf-8") == custom
    assert Path(".gitignore") in result.preserved

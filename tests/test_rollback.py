"""Tests for joinery.rollback — undoing the most recent transaction."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from joinery.adopt import adopt
from joinery.init import scaffold
from joinery.rollback import NoTransactionError, rollback


def _make_existing_project(tmp_path: Path) -> Path:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "main.py").write_text("print('x')\n", encoding="utf-8")
    (target / "README.md").write_text("# existing\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"],
        cwd=target,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
        cwd=target,
        check=True,
        capture_output=True,
    )
    return target


def test_rollback_raises_when_no_transactions(tmp_path: Path) -> None:
    with pytest.raises(NoTransactionError):
        rollback(tmp_path)


def test_rollback_after_init_removes_written_files(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    scaffold(
        target=target, project_name="fresh", tier="standard", language="python", init_git=False
    )
    assert (target / "CLAUDE.md").is_file()
    assert (target / "plan.md").is_file()

    result = rollback(target)
    assert not (target / "CLAUDE.md").exists()
    assert not (target / "plan.md").exists()
    assert "CLAUDE.md" in result.deleted_files


def test_rollback_after_adopt_preserves_user_files(tmp_path: Path) -> None:
    """README.md predates Joinery and should NOT be deleted by rollback."""
    target = _make_existing_project(tmp_path)
    original_readme = (target / "README.md").read_text(encoding="utf-8")

    adopt(target, tier="production", language="python")
    # README.md was preserved during adopt; rollback should leave it intact.
    result = rollback(target)
    assert (target / "README.md").read_text(encoding="utf-8") == original_readme
    # Joinery-written files should be gone now.
    assert not (target / "CLAUDE.md").exists()
    assert "CLAUDE.md" in result.deleted_files


def test_rollback_restores_hooks_from_backup(tmp_path: Path) -> None:
    target = _make_existing_project(tmp_path)
    # Pre-existing user hook
    user_hook = target / ".git" / "hooks" / "pre-commit"
    user_hook.write_text("#!/bin/sh\necho 'mine'\n", encoding="utf-8")

    # --force makes Joinery overwrite the user's hook (otherwise it's preserved).
    # The backup captures the user's original before the overwrite.
    adopt(target, tier="production", language="python", force=True)
    assert "mine" not in user_hook.read_text(encoding="utf-8")

    result = rollback(target)
    # User's hook restored from backup
    assert "mine" in user_hook.read_text(encoding="utf-8")
    assert "pre-commit" in result.restored_hooks


def test_rollback_removes_transaction_file(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    scaffold(
        target=target, project_name="fresh", tier="standard", language="python", init_git=False
    )
    txn_dir = target / ".joinery" / "transactions"
    txns_before = list(txn_dir.glob("*.json"))
    assert len(txns_before) == 1

    rollback(target)
    txns_after = list(txn_dir.glob("*.json"))
    assert len(txns_after) == 0


def test_rollback_keep_files_leaves_written_in_place(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    scaffold(
        target=target, project_name="fresh", tier="standard", language="python", init_git=False
    )
    assert (target / "CLAUDE.md").is_file()

    result = rollback(target, keep_files=True)
    # Files remain
    assert (target / "CLAUDE.md").is_file()
    assert (target / "plan.md").is_file()
    # But the transaction record is gone
    assert result.deleted_files == []


def test_rollback_handles_already_deleted_files_gracefully(tmp_path: Path) -> None:
    target = tmp_path / "fresh"
    scaffold(
        target=target, project_name="fresh", tier="standard", language="python", init_git=False
    )
    # User manually removed a file before rolling back
    (target / "plan.md").unlink()

    result = rollback(target)
    assert "plan.md" in result.missing_files
    # CLAUDE.md should still be deleted normally
    assert "CLAUDE.md" in result.deleted_files

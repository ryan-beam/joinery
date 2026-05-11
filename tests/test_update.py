"""Tests for joinery.update — applying managed-file drift."""

from __future__ import annotations

from pathlib import Path

import pytest

from joinery.diff import NotAdoptedError, diff_managed_files
from joinery.init import scaffold
from joinery.manifest import read_manifest
from joinery.update import apply_updates


def _scaffold(tmp_path: Path) -> Path:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    return target


def test_update_raises_when_no_manifest(tmp_path: Path) -> None:
    target = tmp_path / "x"
    target.mkdir()
    (target / "file.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(NotAdoptedError):
        apply_updates(target)


def test_update_no_op_when_no_drift(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    result = apply_updates(target)
    assert result.applied == []


def test_update_applies_user_edited_file(tmp_path: Path) -> None:
    """A managed file the user edited should be overwritten by update."""
    target = _scaffold(tmp_path)
    claude = target / "CLAUDE.md"
    original = claude.read_text(encoding="utf-8")
    claude.write_text(original + "\n## User edit\n", encoding="utf-8")

    result = apply_updates(target)
    assert "CLAUDE.md" in result.applied
    # File restored to template content (no user edits)
    assert "User edit" not in claude.read_text(encoding="utf-8")


def test_update_restores_missing_managed_file(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    (target / "plan.md").unlink()
    assert not (target / "plan.md").exists()

    result = apply_updates(target)
    assert "plan.md" in result.applied
    assert (target / "plan.md").is_file()


def test_update_dry_run_writes_nothing(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    claude = target / "CLAUDE.md"
    claude.write_text("EDITED\n", encoding="utf-8")

    result = apply_updates(target, dry_run=True)
    assert "CLAUDE.md" in result.applied  # in the would-update list
    assert claude.read_text(encoding="utf-8") == "EDITED\n"  # unchanged


def test_update_records_transaction(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    (target / "plan.md").write_text("EDITED\n", encoding="utf-8")

    txn_dir = target / ".joinery" / "transactions"
    before = len(list(txn_dir.glob("*.json")))
    apply_updates(target)
    after = len(list(txn_dir.glob("*.json")))
    assert after == before + 1


def test_update_refreshes_manifest_version(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    (target / "plan.md").write_text("EDITED\n", encoding="utf-8")

    # Pretend manifest came from an older Joinery: rewrite version
    manifest_path = target / ".workshop" / "answers.toml"
    text = manifest_path.read_text(encoding="utf-8")
    older = text.replace(text.split('joinery_version = "')[1].split('"')[0], "0.0.1")
    manifest_path.write_text(older, encoding="utf-8")

    pre = read_manifest(target)
    assert pre is not None
    assert pre.joinery_version == "0.0.1"

    apply_updates(target)
    post = read_manifest(target)
    assert post is not None
    assert post.joinery_version != "0.0.1"


def test_update_only_filter_restricts_writes(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    (target / "CLAUDE.md").write_text("A\n", encoding="utf-8")
    (target / "plan.md").write_text("B\n", encoding="utf-8")

    result = apply_updates(target, only=["CLAUDE.md"])
    assert "CLAUDE.md" in result.applied
    assert "plan.md" in result.skipped
    # plan.md unchanged
    assert (target / "plan.md").read_text(encoding="utf-8") == "B\n"


def test_update_then_diff_is_clean(tmp_path: Path) -> None:
    """Round-trip: introduce drift, run update, diff should be clean."""
    target = _scaffold(tmp_path)
    (target / "plan.md").write_text("EDITED\n", encoding="utf-8")
    assert diff_managed_files(target).has_drift

    apply_updates(target)
    assert not diff_managed_files(target).has_drift

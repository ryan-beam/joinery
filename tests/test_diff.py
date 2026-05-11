"""Tests for joinery.diff — drift detection on managed files."""

from __future__ import annotations

from pathlib import Path

import pytest

from joinery.diff import NotAdoptedError, diff_managed_files, render_managed_state
from joinery.init import scaffold
from joinery.manifest import read_manifest


def _scaffold(tmp_path: Path) -> Path:
    target = tmp_path / "p"
    scaffold(target=target, project_name="p", tier="standard", language="python", init_git=False)
    return target


def test_diff_raises_when_no_manifest(tmp_path: Path) -> None:
    target = tmp_path / "x"
    target.mkdir()
    (target / "file.py").write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(NotAdoptedError):
        diff_managed_files(target)


def test_diff_clean_state_after_init(tmp_path: Path) -> None:
    """Immediately after init, nothing should be drifted."""
    target = _scaffold(tmp_path)
    report = diff_managed_files(target)
    assert report.drifted == []
    assert report.missing == []
    assert len(report.clean) > 0
    assert not report.has_drift


def test_diff_detects_user_edit_to_managed_file(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    claude = target / "CLAUDE.md"
    claude.write_text(claude.read_text(encoding="utf-8") + "\n## My edits\n", encoding="utf-8")

    report = diff_managed_files(target)
    drifted_paths = [d.rel_path for d in report.drifted]
    assert "CLAUDE.md" in drifted_paths
    # The unified diff should reference the file
    drifted_entry = next(d for d in report.drifted if d.rel_path == "CLAUDE.md")
    assert "CLAUDE.md" in drifted_entry.unified_diff


def test_diff_detects_missing_managed_file(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    (target / "plan.md").unlink()

    report = diff_managed_files(target)
    missing_paths = [d.rel_path for d in report.missing]
    assert "plan.md" in missing_paths


def test_diff_skips_non_rendered_files(tmp_path: Path) -> None:
    """Hooks, skills, usage.jsonl, tier.lock, answers.toml are non-rendered."""
    target = _scaffold(tmp_path)
    report = diff_managed_files(target)
    paths = [d.rel_path for d in report.diffs]
    # These should NOT appear in the rendered-file diff
    for non_rendered in (
        ".workshop/usage.jsonl",
        ".workshop/tier.lock",
        ".workshop/answers.toml",
    ):
        assert non_rendered not in paths


def test_render_managed_state_includes_core_files(tmp_path: Path) -> None:
    target = _scaffold(tmp_path)
    manifest = read_manifest(target)
    assert manifest is not None
    state = render_managed_state(manifest)
    assert "CLAUDE.md" in state
    assert "plan.md" in state
    assert "AGENTS.md" in state
    assert "HANDOVER.md" in state
    assert "README.md" in state
    assert ".workshop/config.toml" in state
    assert "docs/decisions/0001-tier-selection.md" in state


def test_diff_uses_stable_time_context(tmp_path: Path) -> None:
    """Running diff twice in a row should not produce spurious drift."""
    target = _scaffold(tmp_path)
    first = diff_managed_files(target)
    second = diff_managed_files(target)
    assert [d.status for d in first.diffs] == [d.status for d in second.diffs]
    assert not first.has_drift
    assert not second.has_drift

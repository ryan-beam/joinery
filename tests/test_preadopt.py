"""Tests for joinery.preadopt — pre-adopt safety scan + hook backup."""

from __future__ import annotations

import subprocess
from pathlib import Path

from joinery.preadopt import (
    PreAdoptReport,
    UnsafeAdoptError,
    backup_hooks,
    scan,
)


def _make_git_project(tmp_path: Path, *, clean: bool = True) -> Path:
    target = tmp_path / "repo"
    target.mkdir()
    (target / "main.py").write_text("print('hi')\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True)
    if clean:
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


def test_scan_clean_tree_has_no_errors(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    report = scan(target)
    assert report.errors == []


def test_scan_dirty_tree_reports_error(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=False)
    report = scan(target)
    assert any("working tree is dirty" in e for e in report.errors)


def test_scan_non_git_target_does_not_complain_about_dirtiness(tmp_path: Path) -> None:
    """Non-git targets have no working tree concept; dirtiness shouldn't apply."""
    target = tmp_path / "no-git"
    target.mkdir()
    (target / "file.py").write_text("x = 1\n", encoding="utf-8")
    report = scan(target)
    assert not any("working tree is dirty" in e for e in report.errors)


def test_scan_warns_about_env_file(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    (target / ".env").write_text("SECRET=shh\n", encoding="utf-8")
    report = scan(target)
    assert any("sensitive paths present" in w for w in report.warnings)


def test_scan_warns_about_pem_file(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    (target / "server.pem").write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    report = scan(target)
    assert any("sensitive paths present" in w for w in report.warnings)


def test_scan_warns_about_aws_directory(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    (target / ".aws").mkdir()
    report = scan(target)
    assert any(".aws/" in w for w in report.warnings)


def test_scan_warns_when_husky_detected(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    (target / ".husky").mkdir()
    report = scan(target)
    assert any("husky" in w for w in report.warnings)


def test_scan_warns_when_pre_commit_framework_detected(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    (target / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    report = scan(target)
    assert any("pre-commit framework" in w for w in report.warnings)


def test_scan_info_lists_existing_hooks(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    hooks_dir = target / ".git" / "hooks"
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    report = scan(target)
    assert any("pre-commit" in i for i in report.info)


def test_scan_skips_hook_check_when_hooks_disabled(tmp_path: Path) -> None:
    """install_hooks=False means we won't touch .git/hooks — no need to inventory it."""
    target = _make_git_project(tmp_path, clean=True)
    hooks_dir = target / ".git" / "hooks"
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    report = scan(target, install_hooks=False)
    assert report.info == []


def test_scan_ignores_sample_hooks(tmp_path: Path) -> None:
    """`.sample` files are git's defaults — they don't count as user hooks."""
    target = _make_git_project(tmp_path, clean=True)
    hooks_dir = target / ".git" / "hooks"
    # Git init may have written .sample files; explicitly add one if not.
    (hooks_dir / "pre-commit.sample").write_text("#!/bin/sh\n", encoding="utf-8")
    report = scan(target)
    # No real hooks installed yet; .sample shouldn't trigger info.
    assert not any("pre-commit" in i for i in report.info)


def test_backup_hooks_creates_timestamped_directory(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    hooks_dir = target / ".git" / "hooks"
    (hooks_dir / "pre-commit").write_text("#!/bin/sh\necho old\n", encoding="utf-8")
    (hooks_dir / "pre-push").write_text("#!/bin/sh\necho push\n", encoding="utf-8")
    backup = backup_hooks(target)
    assert backup is not None
    assert backup.is_dir()
    assert (backup / "pre-commit").is_file()
    assert (backup / "pre-push").is_file()
    # Backup path is under .joinery/backup/
    assert ".joinery" in backup.parts
    assert "backup" in backup.parts


def test_backup_hooks_returns_none_when_no_hooks(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    backup = backup_hooks(target)
    assert backup is None


def test_backup_hooks_returns_none_when_no_git(tmp_path: Path) -> None:
    target = tmp_path / "plain"
    target.mkdir()
    (target / "file.py").write_text("x = 1", encoding="utf-8")
    assert backup_hooks(target) is None


def test_backup_hooks_ignores_sample_files(tmp_path: Path) -> None:
    target = _make_git_project(tmp_path, clean=True)
    hooks_dir = target / ".git" / "hooks"
    (hooks_dir / "pre-commit.sample").write_text("#!/bin/sh\n", encoding="utf-8")
    assert backup_hooks(target) is None


def test_pre_adopt_report_properties() -> None:
    empty = PreAdoptReport()
    assert not empty.has_errors
    assert not empty.has_findings

    err = PreAdoptReport(errors=["bad"])
    assert err.has_errors
    assert err.has_findings

    warn = PreAdoptReport(warnings=["heads up"])
    assert not warn.has_errors
    assert warn.has_findings


def test_unsafe_adopt_error_carries_report() -> None:
    report = PreAdoptReport(errors=["x"])
    err = UnsafeAdoptError(report)
    assert err.report is report
    assert "Pre-adopt safety scan" in str(err)

"""Tests for joinery.transactions — the append-only transaction log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from joinery.transactions import (
    TRANSACTIONS_RELDIR,
    Transaction,
    latest_transaction,
    list_transactions,
    read_transaction,
    write_transaction,
)


def test_write_transaction_creates_timestamped_file(tmp_path: Path) -> None:
    txn = Transaction(
        mode="init",
        tier="production",
        language="python",
        project_name="hello",
        written_files=["CLAUDE.md", "plan.md"],
        hooks_installed=["pre-commit"],
    )
    path = write_transaction(tmp_path, txn)
    assert path.is_file()
    assert path.parent == tmp_path / TRANSACTIONS_RELDIR
    assert path.suffix == ".json"


def test_write_transaction_fills_timestamp(tmp_path: Path) -> None:
    txn = Transaction(mode="adopt", tier="standard", language="python", project_name="x")
    write_transaction(tmp_path, txn)
    assert txn.timestamp
    assert "T" in txn.timestamp


def test_round_trip(tmp_path: Path) -> None:
    original = Transaction(
        mode="adopt",
        tier="sketch",
        language="typescript",
        project_name="round-trip",
        written_files=["CLAUDE.md", "plan.md"],
        preserved_files=["README.md"],
        hooks_installed=["pre-commit", "pre-push"],
        hooks_backup_path="backup/hooks-2026-01-01",
    )
    path = write_transaction(tmp_path, original)
    loaded = read_transaction(path)
    assert loaded.mode == "adopt"
    assert loaded.tier == "sketch"
    assert loaded.language == "typescript"
    assert loaded.project_name == "round-trip"
    assert loaded.written_files == ["CLAUDE.md", "plan.md"]
    assert loaded.preserved_files == ["README.md"]
    assert loaded.hooks_installed == ["pre-commit", "pre-push"]
    assert loaded.hooks_backup_path == "backup/hooks-2026-01-01"


def test_list_transactions_returns_paths_in_chronological_order(tmp_path: Path) -> None:
    # Manually create three files with explicit, sortable names to avoid timing flakiness.
    txn_dir = tmp_path / TRANSACTIONS_RELDIR
    txn_dir.mkdir(parents=True)
    for stamp in ("20260101T000000Z", "20260201T000000Z", "20260301T000000Z"):
        (txn_dir / f"{stamp}.json").write_text(
            json.dumps(
                {
                    "mode": "init",
                    "tier": "standard",
                    "language": "python",
                    "project_name": "x",
                    "written_files": [],
                    "preserved_files": [],
                    "hooks_installed": [],
                    "hooks_backup_path": None,
                    "joinery_version": "0.1.x",
                    "timestamp": stamp,
                }
            ),
            encoding="utf-8",
        )
    paths = list_transactions(tmp_path)
    assert len(paths) == 3
    assert paths[0].name == "20260101T000000Z.json"
    assert paths[-1].name == "20260301T000000Z.json"


def test_latest_transaction_returns_newest(tmp_path: Path) -> None:
    txn1 = Transaction(
        mode="init",
        tier="standard",
        language="python",
        project_name="old",
        timestamp="2026-01-01T00:00:00+00:00",
    )
    write_transaction(tmp_path, txn1)
    txn2 = Transaction(
        mode="adopt",
        tier="production",
        language="python",
        project_name="newer",
        timestamp="2026-06-01T00:00:00+00:00",
    )
    write_transaction(tmp_path, txn2)
    latest = latest_transaction(tmp_path)
    assert latest is not None
    assert latest.project_name == "newer"


def test_latest_transaction_returns_none_when_empty(tmp_path: Path) -> None:
    assert latest_transaction(tmp_path) is None


def test_list_transactions_returns_empty_when_no_dir(tmp_path: Path) -> None:
    assert list_transactions(tmp_path) == []


def test_read_transaction_rejects_invalid_mode(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "mode": "destroy",
                "tier": "production",
                "language": "python",
                "project_name": "x",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid mode"):
        read_transaction(path)


def test_serialized_json_is_valid(tmp_path: Path) -> None:
    txn = Transaction(mode="init", tier="standard", language="python", project_name="x")
    path = write_transaction(tmp_path, txn)
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed["mode"] == "init"
    assert parsed["project_name"] == "x"

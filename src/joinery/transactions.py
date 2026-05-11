"""Transaction log — append-only audit trail of every adopt/init that wrote files.

Every successful (non-dry-run) `workshop init` or `workshop adopt` writes a
JSON record to `.joinery/transactions/<timestamp>.json`. Each record lists
the files written, the files preserved, the hooks installed, and the path
to any hook backup made during that operation.

The log is append-only — Joinery never modifies an existing transaction. The
`workshop rollback` command reads the most recent record to undo the most
recent operation.

JSON (not TOML) because transaction records are append-only audit data, not
human-edited config; stdlib `json` handles it without a writer dependency.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from joinery import __version__

TRANSACTIONS_RELDIR = Path(".joinery") / "transactions"

Mode = Literal["init", "adopt"]


@dataclass
class Transaction:
    """One record of a Joinery operation that wrote files."""

    mode: Mode
    tier: str
    language: str
    project_name: str
    written_files: list[str] = field(default_factory=list)
    preserved_files: list[str] = field(default_factory=list)
    hooks_installed: list[str] = field(default_factory=list)
    hooks_backup_path: str | None = None
    joinery_version: str = __version__
    timestamp: str = ""  # ISO 8601 UTC, filled by write_transaction() if empty


def write_transaction(target: Path, txn: Transaction) -> Path:
    """Append a transaction record to `<target>/.joinery/transactions/`.

    File name is `<timestamp>.json` with a sortable Z-suffixed UTC stamp so
    `list_transactions()` returns them in chronological order naturally.
    """
    if not txn.timestamp:
        txn.timestamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
    stamp = datetime.fromisoformat(txn.timestamp).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    txn_dir = target / TRANSACTIONS_RELDIR
    txn_dir.mkdir(parents=True, exist_ok=True)
    path = txn_dir / f"{stamp}.json"
    payload: dict[str, Any] = asdict(txn)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_transactions(target: Path) -> list[Path]:
    """Return all transaction-file paths under target, sorted oldest → newest."""
    txn_dir = target / TRANSACTIONS_RELDIR
    if not txn_dir.is_dir():
        return []
    return sorted(p for p in txn_dir.glob("*.json") if p.is_file())


def latest_transaction(target: Path) -> Transaction | None:
    """Return the most recent transaction record, or None if none exist."""
    paths = list_transactions(target)
    if not paths:
        return None
    return _load(paths[-1])


def read_transaction(path: Path) -> Transaction:
    """Read a specific transaction file."""
    return _load(path)


def _load(path: Path) -> Transaction:
    data = json.loads(path.read_text(encoding="utf-8"))
    mode = data["mode"]
    if mode not in ("init", "adopt"):
        raise ValueError(f"Invalid mode in {path}: {mode!r}")
    return Transaction(
        mode=mode,
        tier=str(data["tier"]),
        language=str(data["language"]),
        project_name=str(data["project_name"]),
        written_files=[str(p) for p in data.get("written_files", [])],
        preserved_files=[str(p) for p in data.get("preserved_files", [])],
        hooks_installed=[str(p) for p in data.get("hooks_installed", [])],
        hooks_backup_path=(
            str(data["hooks_backup_path"]) if data.get("hooks_backup_path") is not None else None
        ),
        joinery_version=str(data.get("joinery_version", __version__)),
        timestamp=str(data.get("timestamp", "")),
    )

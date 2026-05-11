"""Rollback the most recent Joinery transaction.

`workshop rollback` reads the latest `.joinery/transactions/<timestamp>.json`,
deletes every file it lists under `written_files` (if the file still exists),
restores any hooks from the recorded backup path, and removes the transaction
record. The operation is bounded to the most recent transaction — there is
no multi-step undo. For older state, use git.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from joinery.transactions import Transaction, latest_transaction, list_transactions


@dataclass
class RollbackResult:
    """Outcome of a rollback() call."""

    deleted_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    restored_hooks: list[str] = field(default_factory=list)
    transaction_path: Path | None = None
    transaction: Transaction | None = None


class NoTransactionError(RuntimeError):
    """Raised when there is no transaction to roll back."""


def rollback(target: Path, *, keep_files: bool = False) -> RollbackResult:
    """Undo the most recent Joinery transaction in `target`.

    Args:
        target: The project root.
        keep_files: If True, restore hooks but leave written files in place.
            Useful for "I want to keep what was scaffolded but disconnect
            from Joinery's transaction log."

    Returns:
        RollbackResult describing what was removed/restored.

    Raises:
        NoTransactionError: if no transactions exist under `target`.
    """
    txn = latest_transaction(target)
    if txn is None:
        raise NoTransactionError(
            f"No Joinery transactions found in {target}. Nothing to roll back."
        )

    paths = list_transactions(target)
    txn_path = paths[-1]
    result = RollbackResult(transaction=txn, transaction_path=txn_path)

    if not keep_files:
        for rel in txn.written_files:
            file_path = target / rel
            if file_path.is_file():
                file_path.unlink()
                result.deleted_files.append(rel)
            else:
                result.missing_files.append(rel)

    if txn.hooks_backup_path:
        result.restored_hooks = _restore_hooks(target, Path(txn.hooks_backup_path))

    # Remove the transaction file. Future-proofing: leave .joinery/ intact
    # in case other state lives there; only delete the single record.
    txn_path.unlink()

    return result


def _restore_hooks(target: Path, backup_dir: Path) -> list[str]:
    """Copy backed-up hooks back into `.git/hooks/`. Returns names restored."""
    if not backup_dir.is_dir():
        return []
    hooks_dir = target / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return []
    restored: list[str] = []
    for hook in backup_dir.iterdir():
        if not hook.is_file():
            continue
        shutil.copy2(hook, hooks_dir / hook.name)
        restored.append(hook.name)
    return restored

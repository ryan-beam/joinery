"""Roborev integration — query unresolved findings from the local SQLite store.

Roborev (github.com/roborev-dev/roborev) stores per-commit code review data in
`~/.roborev/reviews.db`. It intentionally does not surface findings to the
developer beyond writing to its SQLite store + offering the `roborev tui`. That
surfacing is the framework's job.

This module is the pure-Python query layer used by:
- the SessionStart hook (surfaces unresolved findings count at session start)
- `workshop session end` Phase 1 (gate the session-end on unresolved critical/high)
- potentially `workshop doctor` / status surfaces later

The pre-push hook (`hooks/pre-push`) uses a parallel `bash + jq` implementation
because pre-push runs in a pure-shell context. This module is the Python twin.

Design choices:
- Shell out to the `roborev` CLI (`roborev show <sha> --json`) instead of reading
  the SQLite directly. The CLI is the documented stable interface; the DB schema
  is not.
- Graceful degradation: if `roborev` is not on PATH, every public function
  returns an empty/null result without raising. Joinery must work for users who
  don't have roborev installed.
- No `jq` dependency on this side — parse JSON in stdlib `json`.
- Severity vocabulary matches roborev v0.55.0: `critical / high / medium / low`.
  Fall through to the `level` field if `severity` is missing (defensive against
  schema drift).
- Statuses treated as "no longer blocking": `resolved`, `dismissed`, `fixed`.
  Missing status defaults to `open`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field

BLOCKING_SEVERITIES: frozenset[str] = frozenset({"critical", "high"})
RESOLVED_STATUSES: frozenset[str] = frozenset({"resolved", "dismissed", "fixed"})


@dataclass(frozen=True)
class Finding:
    """One unresolved roborev finding on one commit."""

    sha: str
    severity: str
    status: str
    message: str = ""
    file: str = ""
    line: int | None = None


@dataclass(frozen=True)
class FindingsSummary:
    """Aggregate count of unresolved findings across a set of commits."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    affected_shas: tuple[str, ...] = field(default_factory=tuple)

    @property
    def total_blocking(self) -> int:
        """critical + high — the count that gates the pre-push hook + session-end."""
        return self.critical + self.high

    @property
    def is_empty(self) -> bool:
        return (self.critical + self.high + self.medium + self.low) == 0


def is_available() -> bool:
    """True iff the `roborev` CLI is on PATH and answers a version probe."""
    if shutil.which("roborev") is None:
        return False
    try:
        # S603/S607: invoking `roborev` from PATH with fixed args. Same pattern as
        # joinery.git which shells out to `git`. Inputs are controlled.
        result = subprocess.run(  # noqa: S603
            ["roborev", "--version"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _normalize_severity(raw: object) -> str:
    """roborev v0.55.0 emits lowercase severities. Normalize defensively."""
    if not isinstance(raw, str):
        return "low"
    s = raw.strip().lower()
    if s in ("critical", "high", "medium", "low"):
        return s
    # Defensive fallbacks for older roborev versions that used different vocab.
    aliases = {
        "blocker": "critical",
        "major": "high",
        "minor": "medium",
        "info": "low",
        "important": "high",
        "nit": "low",
        "nits": "low",
    }
    return aliases.get(s, "low")


def _normalize_status(raw: object) -> str:
    if not isinstance(raw, str):
        return "open"
    return raw.strip().lower() or "open"


def _query_one(sha: str, *, timeout: float = 5.0) -> list[Finding]:
    """Fetch unresolved findings for one commit via `roborev show <sha> --json`.

    Returns an empty list if:
    - roborev has no review for the sha yet (daemon hasn't processed it)
    - the command fails for any reason
    - the JSON is malformed

    Never raises.
    """
    try:
        # S603/S607: `sha` comes from git rev-list output (controlled). Same
        # pattern as joinery.git's subprocess wrapper.
        result = subprocess.run(  # noqa: S603
            ["roborev", "show", sha, "--json"],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    raw_findings = payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(raw_findings, list):
        return []

    out: list[Finding] = []
    for f in raw_findings:
        if not isinstance(f, dict):
            continue
        severity = _normalize_severity(f.get("severity") or f.get("level"))
        status = _normalize_status(f.get("status"))
        if status in RESOLVED_STATUSES:
            continue
        line_val = f.get("line")
        line_int = line_val if isinstance(line_val, int) else None
        out.append(
            Finding(
                sha=sha,
                severity=severity,
                status=status,
                message=str(f.get("message") or f.get("title") or ""),
                file=str(f.get("file") or f.get("path") or ""),
                line=line_int,
            )
        )
    return out


def query_findings(shas: Iterable[str], *, timeout_each: float = 5.0) -> list[Finding]:
    """Fetch unresolved findings across multiple commits.

    Iterates per-sha; each `roborev show` call is independent. If roborev is
    unavailable, returns []. No exceptions escape.
    """
    if not is_available():
        return []
    seen_shas: set[str] = set()
    out: list[Finding] = []
    for sha in shas:
        sha = (sha or "").strip()
        if not sha or sha in seen_shas:
            continue
        seen_shas.add(sha)
        out.extend(_query_one(sha, timeout=timeout_each))
    return out


def summarize(findings: list[Finding]) -> FindingsSummary:
    """Aggregate a flat findings list into a counts-by-severity summary."""
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    affected: list[str] = []
    seen_shas: set[str] = set()
    for f in findings:
        if f.severity in counts:
            counts[f.severity] += 1
        if f.sha and f.sha not in seen_shas:
            seen_shas.add(f.sha)
            affected.append(f.sha)
    return FindingsSummary(
        critical=counts["critical"],
        high=counts["high"],
        medium=counts["medium"],
        low=counts["low"],
        affected_shas=tuple(affected),
    )


def format_summary(summary: FindingsSummary, *, sha_short: int = 7) -> str:
    """Human-readable one-liner for surfacing in hook output / skill prompts.

    Returns an empty string if there's nothing to report — callers can use that
    to decide whether to emit the line at all.
    """
    if summary.is_empty:
        return ""
    parts: list[str] = []
    if summary.critical:
        parts.append(f"{summary.critical} critical")
    if summary.high:
        parts.append(f"{summary.high} high")
    if summary.medium:
        parts.append(f"{summary.medium} medium")
    if summary.low:
        parts.append(f"{summary.low} low")
    head = ", ".join(parts)
    if summary.affected_shas:
        shorts = [s[:sha_short] for s in summary.affected_shas[:5]]
        suffix = f" (commits {', '.join(shorts)}"
        if len(summary.affected_shas) > 5:
            suffix += f", +{len(summary.affected_shas) - 5} more"
        suffix += ")"
        return head + suffix
    return head

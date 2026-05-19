"""Tests for `joinery.roborev` — the surfacing-layer query module.

Covers the public surface: is_available, query_findings, summarize,
format_summary. Subprocess calls are mocked. No real roborev needed.
"""

from __future__ import annotations

import json
import subprocess
from unittest import mock

from joinery.roborev import (
    BLOCKING_SEVERITIES,
    Finding,
    FindingsSummary,
    format_summary,
    is_available,
    query_findings,
    summarize,
)

# ---------------------------------------------------------------------------
# is_available
# ---------------------------------------------------------------------------


def test_is_available_false_when_roborev_missing() -> None:
    with mock.patch("joinery.roborev.shutil.which", return_value=None):
        assert is_available() is False


def test_is_available_true_when_version_probe_succeeds() -> None:
    with (
        mock.patch(
            "joinery.roborev.shutil.which",
            return_value="/usr/local/bin/roborev",
        ),
        mock.patch(
            "joinery.roborev.subprocess.run",
            return_value=mock.MagicMock(returncode=0, stdout="roborev 0.55.0\n"),
        ),
    ):
        assert is_available() is True


def test_is_available_false_when_version_probe_fails() -> None:
    """A binary that exists but errors on --version is treated as unavailable."""
    with (
        mock.patch(
            "joinery.roborev.shutil.which",
            return_value="/usr/local/bin/roborev",
        ),
        mock.patch(
            "joinery.roborev.subprocess.run",
            return_value=mock.MagicMock(returncode=1, stdout=""),
        ),
    ):
        assert is_available() is False


def test_is_available_false_on_subprocess_exception() -> None:
    """Timeouts / OSError on the probe should not propagate."""
    with (
        mock.patch(
            "joinery.roborev.shutil.which",
            return_value="/usr/local/bin/roborev",
        ),
        mock.patch(
            "joinery.roborev.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="roborev", timeout=5),
        ),
    ):
        assert is_available() is False


# ---------------------------------------------------------------------------
# query_findings — JSON shape parsing + severity/status filtering
# ---------------------------------------------------------------------------


def _mock_show(sha_to_payload: dict[str, dict | None]) -> mock.MagicMock:
    """Helper: stub `subprocess.run` so each `roborev show <sha> --json` call
    returns the payload mapped to that sha. None = simulate empty stdout
    (roborev daemon hasn't processed the sha yet)."""

    def runner(cmd, **kwargs):
        # cmd is ["roborev", "show", "<sha>", "--json"]
        sha = cmd[2]
        payload = sha_to_payload.get(sha)
        if payload is None:
            return mock.MagicMock(returncode=0, stdout="")
        return mock.MagicMock(returncode=0, stdout=json.dumps(payload))

    return mock.MagicMock(side_effect=runner)


def test_query_findings_returns_empty_when_unavailable() -> None:
    """If roborev isn't on PATH, query returns [] without any subprocess calls."""
    with mock.patch("joinery.roborev.is_available", return_value=False):
        result = query_findings(["abc123"])
    assert result == []


def test_query_findings_parses_critical_and_high() -> None:
    payload = {
        "findings": [
            {
                "severity": "critical",
                "status": "open",
                "message": "SQL injection",
                "file": "src/db.py",
                "line": 42,
            },
            {
                "severity": "high",
                "status": "open",
                "message": "missing error handling",
                "file": "src/api.py",
                "line": 17,
            },
        ]
    }
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            _mock_show({"abc123": payload}),
        ),
    ):
        findings = query_findings(["abc123"])

    assert len(findings) == 2
    assert {f.severity for f in findings} == {"critical", "high"}
    sql = next(f for f in findings if f.severity == "critical")
    assert sql.message == "SQL injection"
    assert sql.file == "src/db.py"
    assert sql.line == 42
    assert sql.sha == "abc123"


def test_query_findings_drops_resolved_dismissed_fixed() -> None:
    """Resolved/dismissed/fixed findings must not appear in output."""
    payload = {
        "findings": [
            {"severity": "critical", "status": "open", "message": "real bug"},
            {"severity": "critical", "status": "resolved", "message": "fixed by user"},
            {"severity": "high", "status": "dismissed", "message": "false positive"},
            {"severity": "high", "status": "fixed", "message": "already patched"},
        ]
    }
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            _mock_show({"abc123": payload}),
        ),
    ):
        findings = query_findings(["abc123"])
    assert len(findings) == 1
    assert findings[0].message == "real bug"


def test_query_findings_handles_level_field_fallback() -> None:
    """Older roborev schemas may use `level` instead of `severity`."""
    payload = {"findings": [{"level": "high", "status": "open", "message": "x"}]}
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            _mock_show({"abc123": payload}),
        ),
    ):
        findings = query_findings(["abc123"])
    assert len(findings) == 1
    assert findings[0].severity == "high"


def test_query_findings_handles_missing_status_as_open() -> None:
    """No status field → treat as open (not silently dropped)."""
    payload = {"findings": [{"severity": "critical", "message": "no status field"}]}
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            _mock_show({"abc123": payload}),
        ),
    ):
        findings = query_findings(["abc123"])
    assert len(findings) == 1
    assert findings[0].status == "open"


def test_query_findings_returns_empty_for_no_review_yet() -> None:
    """Empty stdout = roborev hasn't reviewed the sha. Don't fabricate findings."""
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            _mock_show({"abc123": None}),
        ),
    ):
        findings = query_findings(["abc123"])
    assert findings == []


def test_query_findings_swallows_malformed_json() -> None:
    """Garbage stdout shouldn't crash the caller."""
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            return_value=mock.MagicMock(returncode=0, stdout="{not valid json"),
        ),
    ):
        findings = query_findings(["abc123"])
    assert findings == []


def test_query_findings_swallows_subprocess_exception() -> None:
    """Timeout or OSError on per-sha call shouldn't propagate."""
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch(
            "joinery.roborev.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="roborev", timeout=5),
        ),
    ):
        findings = query_findings(["abc123"])
    assert findings == []


def test_query_findings_dedupes_repeated_shas() -> None:
    """If the caller passes the same sha twice, only query roborev once."""
    payload = {"findings": [{"severity": "critical", "status": "open"}]}
    runner = _mock_show({"abc123": payload})
    with (
        mock.patch("joinery.roborev.is_available", return_value=True),
        mock.patch("joinery.roborev.subprocess.run", runner),
    ):
        findings = query_findings(["abc123", "abc123", "abc123"])
    # Both findings are for the same sha — they should NOT be duplicated
    # because we de-dupe the sha list before querying. One subprocess call.
    assert len(findings) == 1
    assert runner.call_count == 1


# ---------------------------------------------------------------------------
# summarize + format_summary
# ---------------------------------------------------------------------------


def test_summarize_counts_by_severity_and_collects_shas() -> None:
    findings = [
        Finding(sha="aaa", severity="critical", status="open"),
        Finding(sha="aaa", severity="high", status="open"),
        Finding(sha="bbb", severity="critical", status="open"),
        Finding(sha="bbb", severity="medium", status="open"),
        Finding(sha="ccc", severity="low", status="open"),
    ]
    summary = summarize(findings)
    assert summary.critical == 2
    assert summary.high == 1
    assert summary.medium == 1
    assert summary.low == 1
    assert summary.total_blocking == 3  # 2 critical + 1 high
    assert summary.affected_shas == ("aaa", "bbb", "ccc")
    assert summary.is_empty is False


def test_summarize_empty_input_is_empty() -> None:
    summary = summarize([])
    assert summary.is_empty is True
    assert summary.total_blocking == 0


def test_format_summary_empty_returns_empty_string() -> None:
    """Empty summary → caller can use the empty string to skip the surface line."""
    assert format_summary(FindingsSummary()) == ""


def test_format_summary_blocking_findings_show_critical_first() -> None:
    summary = FindingsSummary(
        critical=2, high=1, affected_shas=("abc1234", "def5678")
    )
    line = format_summary(summary)
    assert "2 critical" in line
    assert "1 high" in line
    assert line.index("critical") < line.index("high")
    assert "abc1234" in line
    assert "def5678" in line


def test_format_summary_truncates_sha_list_above_five() -> None:
    summary = FindingsSummary(
        critical=1, affected_shas=tuple(f"sha{i:07d}" for i in range(8))
    )
    line = format_summary(summary)
    assert "+3 more" in line  # 8 affected, shows first 5, says "+3 more"


def test_blocking_severities_constant_is_locked_to_critical_high() -> None:
    """Lock in the gate semantics — pre-push hook + Phase 1 both depend on this."""
    assert BLOCKING_SEVERITIES == frozenset({"critical", "high"})

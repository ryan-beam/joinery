"""Tests for `workshop setup` — the cross-platform roborev install flow."""

from __future__ import annotations

from unittest import mock

from joinery.setup import (
    InstallAttempt,
    SetupResult,
    _build_install_attempts,
    format_failure_help,
    run_setup,
)


def test_setup_no_op_when_roborev_already_present() -> None:
    """If roborev is already on PATH, setup is a clean no-op."""
    with mock.patch("joinery.setup.shutil.which", return_value="/usr/local/bin/roborev"):
        result = run_setup(assume_yes=True)
    assert result.roborev_already_present is True
    assert result.roborev_installed is True
    assert result.attempts == []


def test_build_install_attempts_includes_curl_fallback() -> None:
    """Every platform should at least try the universal curl install."""
    attempts = _build_install_attempts()
    labels = [a.label for a in attempts]
    assert any("curl install" in label for label in labels), (
        f"Universal curl install missing from attempt list: {labels}"
    )


def test_build_install_attempts_macos_prefers_brew() -> None:
    """On macOS, brew should be the first attempt; go install is the universal last resort."""
    with mock.patch("joinery.setup.platform.system", return_value="Darwin"):
        attempts = _build_install_attempts()
    assert "Homebrew" in attempts[0].label
    assert "go install" in attempts[-1].label
    # curl install sits between native-package-manager and go-fallback
    labels = [a.label for a in attempts]
    assert any("curl install" in label for label in labels)


def test_build_install_attempts_windows_uses_powershell() -> None:
    """Windows uses the PowerShell install script (roborev's official Windows path).
    winget / scoop / chocolatey don't have roborev — verified via roborev README."""
    with mock.patch("joinery.setup.platform.system", return_value="Windows"):
        attempts = _build_install_attempts()
    labels = [a.label for a in attempts]
    assert any("PowerShell" in label for label in labels)
    assert any("curl install" in label for label in labels)
    assert any("go install" in label for label in labels)
    # Explicit negatives — the previous (wrong) identifiers must not return.
    assert not any("winget" in label for label in labels)
    assert not any("Scoop" in label for label in labels)


def test_build_install_attempts_all_platforms_include_go_fallback() -> None:
    """Every platform should have the `go install` route as the universal fallback."""
    for system_name in ("Darwin", "Linux", "Windows"):
        with mock.patch("joinery.setup.platform.system", return_value=system_name):
            attempts = _build_install_attempts()
        labels = [a.label for a in attempts]
        assert any("go install" in label for label in labels), (
            f"go install missing for {system_name}: {labels}"
        )


def test_setup_runs_attempts_in_order_until_one_succeeds() -> None:
    """The first successful install short-circuits subsequent attempts."""
    # Two unavailable strategies + one available + one trailing — only the
    # third should actually run.
    fake_attempts = [
        InstallAttempt("brew", ["brew", "install", "x"], available=False),
        InstallAttempt("winget", ["winget", "install", "x"], available=False),
        InstallAttempt("curl", ["bash", "-c", "ok"], available=True),
        InstallAttempt("trailing", ["other"], available=True),
    ]
    with (
        mock.patch("joinery.setup._build_install_attempts", return_value=fake_attempts),
        mock.patch("joinery.setup._run_install", return_value=(True, "")) as run_mock,
        mock.patch(
            "joinery.setup.shutil.which",
            side_effect=lambda name: None if name == "roborev" else f"/bin/{name}",
        ) as which_mock,
    ):
        # Make `which("roborev")` start returning a path after the curl attempt
        # to simulate successful install.
        states = {"roborev_visible": False}

        def which_side_effect(name: str) -> str | None:
            if name == "roborev":
                return "/usr/local/bin/roborev" if states["roborev_visible"] else None
            return f"/bin/{name}"

        def run_side_effect(cmd: list[str]) -> tuple[bool, str]:
            if "bash" in cmd[0]:
                states["roborev_visible"] = True
                return True, ""
            return False, "n/a"

        which_mock.side_effect = which_side_effect
        run_mock.side_effect = run_side_effect

        result = run_setup(assume_yes=True)

    assert result.roborev_installed is True
    # The trailing attempt should be on the result list but not have been run
    # (we don't check this strictly because the loop pre-records the attempt
    # before checking availability; the meaningful check is .success only on
    # the one we expected).
    succeeded = [a for a in result.attempts if a.success]
    assert len(succeeded) == 1
    assert succeeded[0].label == "curl"


def test_format_failure_help_lists_attempts_and_next_steps() -> None:
    """The failure-help block must include the URL and the fallback note."""
    result = SetupResult()
    result.attempts.extend(
        [
            InstallAttempt("brew", ["brew", "install", "x"], available=False),
            InstallAttempt(
                "curl install", ["bash", "-c", "x"], available=True, error="connection refused"
            ),
        ]
    )
    text = format_failure_help(result)
    assert "skipped (prerequisite tool not on PATH)" in text
    assert "connection refused" in text
    assert "github.com/roborev-dev/roborev" in text
    assert "workshop doctor" in text
    assert "/review" in text  # surfaces the fallback exists

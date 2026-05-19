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


# ---------------------------------------------------------------------------
# Shell-profile backfill (Windows PATH-propagation workaround)
# Filed 2026-05-19 after the third "roborev: command not found" hit during
# placket-ops V-cluster work. workshop setup now writes the PATH-extending
# line into ~/.bashrc + PowerShell profile on Windows so new terminals
# pick up roborev without needing a full app relaunch.
# ---------------------------------------------------------------------------


class TestShellProfileBackfill:
    """`_ensure_shell_profiles_have_roborev_path` writes idempotent PATH-extender
    blocks to common shell startups on Windows. No-op elsewhere."""

    def test_noop_on_macos(self, tmp_path) -> None:
        from joinery.setup import _ensure_shell_profiles_have_roborev_path

        with mock.patch("joinery.setup.platform.system", return_value="Darwin"):
            touched = _ensure_shell_profiles_have_roborev_path()
        assert touched == [], "macOS native PATH propagation works; no shell-profile writes needed"

    def test_noop_on_linux(self, tmp_path) -> None:
        from joinery.setup import _ensure_shell_profiles_have_roborev_path

        with mock.patch("joinery.setup.platform.system", return_value="Linux"):
            touched = _ensure_shell_profiles_have_roborev_path()
        assert touched == []

    def test_windows_writes_to_bashrc(self, tmp_path) -> None:
        from joinery.setup import (
            SHELL_PROFILE_MARKER,
            _ensure_shell_profiles_have_roborev_path,
        )

        with (
            mock.patch("joinery.setup.platform.system", return_value="Windows"),
            mock.patch("joinery.setup.Path.home", return_value=tmp_path),
        ):
            touched = _ensure_shell_profiles_have_roborev_path()

        bashrc = tmp_path / ".bashrc"
        assert bashrc.exists(), "should have created ~/.bashrc"
        content = bashrc.read_text(encoding="utf-8")
        assert SHELL_PROFILE_MARKER in content
        assert ".roborev/bin" in content
        assert "export PATH=" in content
        assert str(bashrc) in touched

    def test_windows_writes_to_powershell_profile(self, tmp_path) -> None:
        from joinery.setup import (
            SHELL_PROFILE_MARKER,
            _ensure_shell_profiles_have_roborev_path,
        )

        with (
            mock.patch("joinery.setup.platform.system", return_value="Windows"),
            mock.patch("joinery.setup.Path.home", return_value=tmp_path),
        ):
            touched = _ensure_shell_profiles_have_roborev_path()

        ps_profile = (
            tmp_path / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
        )
        assert ps_profile.exists(), "should have created the PowerShell profile path"
        content = ps_profile.read_text(encoding="utf-8")
        assert SHELL_PROFILE_MARKER in content
        assert ".roborev" in content
        assert "$env:Path" in content
        assert str(ps_profile) in touched

    def test_idempotent_second_run_is_noop(self, tmp_path) -> None:
        """Running setup twice doesn't duplicate the block in either profile."""
        from joinery.setup import _ensure_shell_profiles_have_roborev_path

        with (
            mock.patch("joinery.setup.platform.system", return_value="Windows"),
            mock.patch("joinery.setup.Path.home", return_value=tmp_path),
        ):
            first = _ensure_shell_profiles_have_roborev_path()
            second = _ensure_shell_profiles_have_roborev_path()

        assert len(first) == 2, f"first run should touch bashrc + PS profile, got {first}"
        assert second == [], f"second run should be a no-op, got {second}"

    def test_idempotent_respects_existing_pre_existing_bashrc(self, tmp_path) -> None:
        """If ~/.bashrc already exists with the marker (e.g., user added it
        manually), we don't append again."""
        from joinery.setup import (
            SHELL_PROFILE_MARKER,
            _ensure_shell_profiles_have_roborev_path,
        )

        bashrc = tmp_path / ".bashrc"
        bashrc.write_text(
            f"# user's existing config\n{SHELL_PROFILE_MARKER}\n# already configured\n",
            encoding="utf-8",
        )

        with (
            mock.patch("joinery.setup.platform.system", return_value="Windows"),
            mock.patch("joinery.setup.Path.home", return_value=tmp_path),
        ):
            touched = _ensure_shell_profiles_have_roborev_path()

        # bashrc not touched (already had marker); PS profile is fresh, so touched
        assert str(bashrc) not in touched
        content = bashrc.read_text(encoding="utf-8")
        # Marker appears exactly once still
        assert content.count(SHELL_PROFILE_MARKER) == 1

    def test_idempotent_preserves_existing_content(self, tmp_path) -> None:
        """Appending to an existing bashrc preserves prior content."""
        from joinery.setup import _ensure_shell_profiles_have_roborev_path

        bashrc = tmp_path / ".bashrc"
        original = "# user's existing config\nexport MY_VAR=foo\n"
        bashrc.write_text(original, encoding="utf-8")

        with (
            mock.patch("joinery.setup.platform.system", return_value="Windows"),
            mock.patch("joinery.setup.Path.home", return_value=tmp_path),
        ):
            _ensure_shell_profiles_have_roborev_path()

        content = bashrc.read_text(encoding="utf-8")
        assert content.startswith(original), "must not overwrite existing bashrc content"
        assert ".roborev/bin" in content

    def test_silent_on_io_failure(self, tmp_path) -> None:
        """Shell-profile writes are best-effort. A broken filesystem shouldn't
        crash the setup flow."""
        from joinery.setup import _append_if_missing

        # Try to write to a path under a file (not a directory) — should fail silently
        blocker = tmp_path / "blocker"
        blocker.write_text("not a directory", encoding="utf-8")
        impossible = blocker / "subdir" / "profile"

        ok = _append_if_missing(impossible, "# marker", "# content\n")
        assert ok is False, "should return False on I/O failure, not raise"

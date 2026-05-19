"""`workshop setup` — one-time global setup for Joinery.

Installs external tools Joinery integrates with — primarily roborev (the
adversarial review engine) — using whichever package manager / shell is
available on the host. Cross-platform: macOS / Linux / Windows all covered
via a multi-strategy install with graceful fallback.

This command is idempotent: running it twice does nothing the second time
if everything's already installed.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstallAttempt:
    """One install path tried during setup."""

    label: str
    command: list[str]
    available: bool
    success: bool = False
    error: str = ""


@dataclass
class SetupResult:
    """Summary of a workshop setup run."""

    roborev_installed: bool = False
    roborev_already_present: bool = False
    roborev_init_run: bool = False
    roborev_init_error: str = ""
    shell_profiles_updated: list[str] = None  # type: ignore[assignment]
    attempts: list[InstallAttempt] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.attempts is None:
            self.attempts = []
        if self.shell_profiles_updated is None:
            self.shell_profiles_updated = []


SHELL_PROFILE_MARKER = "# Roborev (added by `workshop setup`)"


def _ensure_shell_profiles_have_roborev_path() -> list[str]:
    """Append a PATH-extending line to common shell startup files on Windows.

    On Windows, `workshop setup` runs roborev's installer which adds
    `%USERPROFILE%\\.roborev\\bin` to the User-level PATH. The problem: Windows
    only propagates User PATH changes to NEWLY-STARTED terminal applications,
    not to existing sessions (or even new tabs in an already-open Windows
    Terminal / Cursor / VS Code). Result: users get `roborev: command not
    found` until they fully quit + relaunch every terminal app, which they
    never figure out from the install output.

    This function papers over that by appending a PATH-extending line to:
      - `~/.bashrc` (Git Bash / WSL)
      - `$PROFILE` for PowerShell (Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1)

    Each line is idempotent (checks for `~/.roborev/bin` already on PATH before
    extending), and the function itself is idempotent — it scans for an existing
    SHELL_PROFILE_MARKER comment before appending.

    Returns the list of profile paths that were touched (empty if all were
    already configured or if not on Windows).

    On macOS/Linux, native PATH propagation works correctly and `brew` / the
    curl installer handle this themselves. No-op there.
    """
    if platform.system() != "Windows":
        return []

    touched: list[str] = []
    home = Path.home()

    # Git Bash / WSL
    bashrc = home / ".bashrc"
    bashrc_block = (
        f"\n{SHELL_PROFILE_MARKER}\n"
        "# Adds roborev to PATH for Git Bash sessions. Idempotent: only extends\n"
        "# PATH if the dir exists and isn't already in PATH. Workaround for\n"
        "# Windows User-PATH not propagating to existing terminal app sessions.\n"
        'if [ -d "$HOME/.roborev/bin" ] && [[ ":$PATH:" != *":$HOME/.roborev/bin:"* ]]; then\n'
        '    export PATH="$PATH:$HOME/.roborev/bin"\n'
        "fi\n"
    )
    if _append_if_missing(bashrc, SHELL_PROFILE_MARKER, bashrc_block):
        touched.append(str(bashrc))

    # PowerShell — $PROFILE default location on Windows
    ps_profile = home / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"
    ps_block = (
        f"\n{SHELL_PROFILE_MARKER}\n"
        "# Adds roborev to PATH for PowerShell sessions. Idempotent: only\n"
        "# extends PATH if the dir exists and isn't already in PATH. Workaround\n"
        "# for Windows User-PATH not propagating to existing terminal sessions.\n"
        '$roborevBin = Join-Path $HOME ".roborev\\bin"\n'
        'if ((Test-Path $roborevBin) -and ($env:Path -notlike "*$roborevBin*")) {\n'
        '    $env:Path += ";$roborevBin"\n'
        "}\n"
    )
    if _append_if_missing(ps_profile, SHELL_PROFILE_MARKER, ps_block):
        touched.append(str(ps_profile))

    return touched


def _append_if_missing(path: Path, marker: str, content: str) -> bool:
    """Append `content` to `path` only if `marker` isn't already in the file.

    Creates parent dirs + the file if missing. Returns True if it wrote.
    Returns False on any I/O failure (silent — shell-profile updates are
    best-effort, never block the setup flow).
    """
    try:
        if path.exists():
            existing = path.read_text(encoding="utf-8", errors="ignore")
            if marker in existing:
                return False
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            existing = ""
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        return True
    except OSError:
        return False


def run_roborev_init(project_root: Path) -> tuple[bool, str]:
    """Run `roborev init` inside a project to install its post-commit hook.

    Returns (success, error_text). Idempotent — running twice is safe; roborev's
    init is a no-op if hooks are already installed.
    """
    if not shutil.which("roborev"):
        return False, "roborev not on PATH"
    if not (project_root / ".git").is_dir():
        return False, "not a git repo"
    try:
        # S603/S607: roborev is on PATH (we just verified with shutil.which); fixed args.
        result = subprocess.run(  # noqa: S603
            ["roborev", "init"],  # noqa: S607
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "(no output)")[:500]


def run_setup(*, assume_yes: bool = False, project_root: Path | None = None) -> SetupResult:
    """Run the global setup flow.

    Args:
        assume_yes: If True, install without prompting (for CI / scripted use).
            Default False — interactive consent prompts before any install.
        project_root: Optional project to also configure post-install. Reserved
            for future per-project setup steps.
    """
    _ = project_root  # reserved
    result = SetupResult()

    if shutil.which("roborev"):
        result.roborev_already_present = True
        result.roborev_installed = True
        return result

    if not assume_yes:
        # CLI layer handles the prompt; this function just builds the attempt list
        # and runs it. The prompt happens in cli.py before calling run_setup with
        # assume_yes=True.
        pass

    for attempt in _build_install_attempts():
        result.attempts.append(attempt)
        if not attempt.available:
            continue
        ok, err = _run_install(attempt.command)
        attempt.success = ok
        attempt.error = err
        if ok and shutil.which("roborev"):
            result.roborev_installed = True
            # Windows PATH propagation gotcha: roborev's installer adds
            # ~/.roborev/bin to User PATH but existing terminal apps don't see
            # it until full app relaunch. Backfill into common shell profiles
            # so new Git Bash + PowerShell sessions see roborev immediately.
            # No-op on macOS/Linux (native PATH handling works).
            result.shell_profiles_updated = _ensure_shell_profiles_have_roborev_path()
            # If the caller passed a project_root, also run `roborev init` to
            # install the post-commit hook in that project.
            if project_root is not None and (project_root / ".git").is_dir():
                init_ok, init_err = run_roborev_init(project_root)
                result.roborev_init_run = init_ok
                result.roborev_init_error = init_err
            return result

    return result


def _build_install_attempts() -> list[InstallAttempt]:
    """Compose the platform-appropriate list of install attempts.

    Order: native package manager (per-platform) → universal curl install.
    Each attempt is independently considered "available" based on whether
    its prerequisite tool (brew, winget, scoop, curl+bash) is on PATH.
    """
    system = platform.system()
    attempts: list[InstallAttempt] = []

    if system == "Darwin":
        attempts.append(
            InstallAttempt(
                label="Homebrew tap (macOS native)",
                command=["brew", "install", "roborev-dev/tap/roborev"],
                available=shutil.which("brew") is not None,
            )
        )
    elif system == "Linux":
        attempts.append(
            InstallAttempt(
                label="Homebrew on Linux (linuxbrew)",
                command=["brew", "install", "roborev-dev/tap/roborev"],
                available=shutil.which("brew") is not None,
            )
        )
    elif system == "Windows":
        attempts.append(
            InstallAttempt(
                label="PowerShell install script (Windows native)",
                command=[
                    "powershell",
                    "-ExecutionPolicy",
                    "ByPass",
                    "-c",
                    "irm https://roborev.io/install.ps1 | iex",
                ],
                available=shutil.which("powershell") is not None,
            )
        )

    # Universal curl install — works on macOS and Linux. (Windows users get the
    # PowerShell script above; if they have Git Bash + curl, this can still work
    # as a secondary attempt.)
    attempts.append(
        InstallAttempt(
            label="curl install script (POSIX shell)",
            command=[
                "bash",
                "-c",
                "curl -fsSL https://roborev.io/install.sh | bash",
            ],
            available=(shutil.which("curl") is not None and shutil.which("bash") is not None),
        )
    )

    # Final fallback: `go install` — works for anyone with Go 1.25+ toolchain.
    attempts.append(
        InstallAttempt(
            label="go install (any platform with Go 1.25+)",
            command=[
                "go",
                "install",
                "github.com/roborev-dev/roborev/cmd/roborev@latest",
            ],
            available=shutil.which("go") is not None,
        )
    )

    return attempts


def _run_install(command: list[str]) -> tuple[bool, str]:
    """Run an install command. Returns (success, error_text).

    Bounded to 300s so a stuck network doesn't hang the user forever.
    Captures stderr for diagnostic surfacing.
    """
    try:
        # S603: command is built from our hardcoded _build_install_attempts list; not user input.
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "(no output)")[:500]


def format_failure_help(result: SetupResult) -> str:
    """Build a user-facing diagnostic block when all attempts failed."""
    lines = [
        "Joinery couldn't install roborev automatically on this machine.",
        "",
        "What was tried:",
    ]
    for a in result.attempts:
        if not a.available:
            lines.append(f"  - {a.label}: skipped (prerequisite tool not on PATH)")
            continue
        if a.success:
            lines.append(f"  - {a.label}: SUCCESS")
        else:
            err = a.error.strip().splitlines()[0] if a.error.strip() else "non-zero exit"
            lines.append(f"  - {a.label}: failed ({err})")
    lines.extend(
        [
            "",
            "Next steps:",
            "  1. Visit https://github.com/roborev-dev/roborev for current install instructions",
            "  2. Install roborev manually for your platform",
            "  3. Re-run `workshop doctor` to verify",
            "",
            "The framework still works without roborev — `/review` falls back to",
            "Claude Code's built-in review skill. Auto-fire on every commit is the",
            "behavior that requires roborev specifically.",
        ]
    )
    return "\n".join(lines)

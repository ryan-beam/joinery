"""`workshop init` — scaffold a new Joinery project.

Reads tier-variant templates from templates/, installs hooks from hooks/,
copies skills from skills/, renders all `{{var}}` placeholders, initializes
git, and creates an initial commit.

The file-laying helpers (`write_project_files`, `write_learning_module`, etc.)
are also imported by `adopt.py`, which uses them with `skip_existing=True`
to overlay the framework onto an existing codebase without disturbing files
that are already there.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from joinery import git
from joinery.lang import Language, detect_language
from joinery.paths import hooks_dir, skills_dir, templates_dir
from joinery.templates import (
    copy_static,
    copy_template,
    copy_tree,
    render_context,
    select_config_template,
)

PROJECT_TEMPLATES: tuple[str, ...] = (
    "CLAUDE.md.starter",
    "plan.md.template",
    "HANDOVER.md.template",
    "README.md.template",
    "AGENTS.md.template",
)

HOOK_NAMES: tuple[str, ...] = (
    "pre-commit",
    "pre-push",
    "commit-msg",
    "post-merge",
)


def write_project_files(
    target: Path, ctx: dict[str, Any], *, skip_existing: bool = False
) -> tuple[list[Path], list[Path]]:
    """Write CLAUDE.md, plan.md, HANDOVER.md, README.md, AGENTS.md from templates."""
    written: list[Path] = []
    preserved: list[Path] = []
    src_templates = templates_dir()
    for tpl_name in PROJECT_TEMPLATES:
        src = src_templates / tpl_name
        if not src.is_file():
            continue
        target_name = _strip_template_suffix(tpl_name)
        dest = target / target_name
        rel = dest.relative_to(target)
        if copy_template(src, dest, ctx, skip_existing=skip_existing):
            written.append(rel)
        else:
            preserved.append(rel)
    return written, preserved


def write_learning_module(
    target: Path, ctx: dict[str, Any], *, skip_existing: bool = False
) -> tuple[list[Path], list[Path]]:
    """Write the learning/ module templates."""
    learning_src = templates_dir() / "learning"
    if not learning_src.is_dir():
        return [], []
    written, preserved = copy_tree(
        learning_src, target / "learning", ctx, skip_existing=skip_existing
    )
    # copy_tree returns paths relative to its target_dir (learning/); re-root to project.
    return (
        [Path("learning") / p for p in written],
        [Path("learning") / p for p in preserved],
    )


def write_tier_adr(
    target: Path, ctx: dict[str, Any], *, skip_existing: bool = False
) -> tuple[list[Path], list[Path]]:
    """Write the tier-selection ADR (docs/decisions/0001-tier-selection.md)."""
    adr_src = templates_dir() / "docs" / "decisions" / "0001-tier-selection.md.template"
    if not adr_src.is_file():
        return [], []
    adr_dest = target / "docs" / "decisions" / "0001-tier-selection.md"
    rel = adr_dest.relative_to(target)
    if copy_template(adr_src, adr_dest, ctx, skip_existing=skip_existing):
        return [rel], []
    return [], [rel]


def write_workshop_state(
    target: Path, tier: str, ctx: dict[str, Any], *, skip_existing: bool = False
) -> tuple[list[Path], list[Path]]:
    """Write .workshop/config.toml, .workshop/usage.jsonl, .workshop/tier.lock."""
    written: list[Path] = []
    preserved: list[Path] = []

    config_src = select_config_template(tier)
    config_dest = target / ".workshop" / "config.toml"
    rel = config_dest.relative_to(target)
    if copy_template(config_src, config_dest, ctx, skip_existing=skip_existing):
        written.append(rel)
    else:
        preserved.append(rel)

    usage_log = target / ".workshop" / "usage.jsonl"
    rel = usage_log.relative_to(target)
    if skip_existing and usage_log.exists():
        preserved.append(rel)
    else:
        usage_log.parent.mkdir(parents=True, exist_ok=True)
        usage_log.write_text("", encoding="utf-8")
        written.append(rel)

    tier_lock = target / ".workshop" / "tier.lock"
    rel = tier_lock.relative_to(target)
    if skip_existing and tier_lock.exists():
        preserved.append(rel)
    else:
        tier_lock.parent.mkdir(parents=True, exist_ok=True)
        tier_lock.write_text(tier + "\n", encoding="utf-8")
        written.append(rel)

    return written, preserved


def install_skills(target: Path, *, skip_existing: bool = False) -> tuple[list[Path], list[Path]]:
    """Copy skills/*.md into .claude/skills/ for Claude Code recognition."""
    written: list[Path] = []
    preserved: list[Path] = []
    skills_src = skills_dir()
    if not skills_src.is_dir():
        return written, preserved
    for skill_file in sorted(skills_src.glob("*.md")):
        if skill_file.name == "README.md":
            continue  # placeholder, not a real skill
        dest = target / ".claude" / "skills" / skill_file.name
        rel = dest.relative_to(target)
        if skip_existing and dest.exists():
            preserved.append(rel)
            continue
        copy_static(skill_file, dest)
        written.append(rel)
    return written, preserved


def install_hooks_into(
    target: Path, *, skip_existing: bool = False
) -> tuple[list[Path], list[Path]]:
    """Install git hooks into .git/hooks/.

    Requires the target to be a git repo (.git/ exists). Caller is responsible
    for that check; this helper raises FileNotFoundError if the dir is missing.
    """
    hooks_target_dir = target / ".git" / "hooks"
    if not hooks_target_dir.is_dir():
        raise FileNotFoundError(
            f".git/hooks/ not found in {target}. Run `git init` first or use adopt --no-hooks."
        )
    written: list[Path] = []
    preserved: list[Path] = []
    hooks_src = hooks_dir()
    for hook_name in HOOK_NAMES:
        hook_file = hooks_src / hook_name
        if not hook_file.is_file():
            continue
        hook_target = hooks_target_dir / hook_name
        rel = hook_target.relative_to(target)
        if skip_existing and hook_target.exists():
            preserved.append(rel)
            continue
        git.install_hook(hook_file, target)
        written.append(rel)
    return written, preserved


def scaffold(
    target: Path,
    project_name: str,
    tier: str,
    language: str,
    init_git: bool = True,
) -> list[Path]:
    """Scaffold a new project at the target path. Returns list of files created."""
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(
            f"Directory `{target}` already exists and is not empty. "
            f"Pick a different name or remove the directory first."
        )
    target.mkdir(parents=True, exist_ok=True)

    ctx = render_context(project_name=project_name, tier=tier, language=language)

    written: list[Path] = []
    written += write_project_files(target, ctx)[0]
    written += write_learning_module(target, ctx)[0]
    written += write_tier_adr(target, ctx)[0]
    written += write_workshop_state(target, tier, ctx)[0]
    written += install_skills(target)[0]

    if init_git:
        git.init_repo(target)
        written += install_hooks_into(target)[0]
        git.add_all(target)
        commit_msg = f"joinery: bench setup, tier={tier}"
        git.commit(target, commit_msg)

    return written


def _strip_template_suffix(filename: str) -> str:
    for suffix in (".template", ".starter", ".global"):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return filename


def language_at_init(cwd: Path, lang_flag: str | None) -> Language:
    """Resolve the language to use for scaffolding."""
    if lang_flag:
        if lang_flag not in ("python", "typescript", "polyglot"):
            raise ValueError(f"Invalid language: {lang_flag!r}")
        return lang_flag  # type: ignore[return-value]
    detected = detect_language(cwd)
    if detected is None:
        return "python"  # default for empty greenfield directories
    return detected

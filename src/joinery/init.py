"""`workshop init` — scaffold a new Joinery project.

Reads tier-variant templates from templates/, installs hooks from hooks/,
copies skills from skills/, renders all `{{var}}` placeholders, initializes
git, and creates an initial commit.
"""

from __future__ import annotations

from pathlib import Path

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
    src_templates = templates_dir()

    # Project-level templates (CLAUDE.md, plan.md, HANDOVER.md, README.md, AGENTS.md)
    for tpl_name in (
        "CLAUDE.md.starter",
        "plan.md.template",
        "HANDOVER.md.template",
        "README.md.template",
        "AGENTS.md.template",
    ):
        src = src_templates / tpl_name
        if src.is_file():
            target_name = _strip_template_suffix(tpl_name)
            dest = target / target_name
            copy_template(src, dest, ctx)
            written.append(dest.relative_to(target))

    # Learning module (skip if sketch tier disables it; for now scaffold all)
    learning_src = src_templates / "learning"
    if learning_src.is_dir():
        written.extend(_relative_all(target, copy_tree(learning_src, target / "learning", ctx)))

    # Tier-selection ADR
    adr_src = src_templates / "docs" / "decisions" / "0001-tier-selection.md.template"
    if adr_src.is_file():
        adr_dest = target / "docs" / "decisions" / "0001-tier-selection.md"
        copy_template(adr_src, adr_dest, ctx)
        written.append(adr_dest.relative_to(target))

    # framework.config.toml (tier-specific)
    config_src = select_config_template(tier)
    config_dest = target / ".workshop" / "config.toml"
    copy_template(config_src, config_dest, ctx)
    written.append(config_dest.relative_to(target))

    # Empty usage.jsonl and tier.lock
    usage_log = target / ".workshop" / "usage.jsonl"
    usage_log.write_text("", encoding="utf-8")
    written.append(usage_log.relative_to(target))

    tier_lock = target / ".workshop" / "tier.lock"
    tier_lock.write_text(tier + "\n", encoding="utf-8")
    written.append(tier_lock.relative_to(target))

    # Copy skills/ into .claude/skills/ for Claude Code recognition
    skills_src = skills_dir()
    if skills_src.is_dir():
        for skill_file in sorted(skills_src.glob("*.md")):
            if skill_file.name == "README.md":
                continue  # placeholder, not a real skill
            dest = target / ".claude" / "skills" / skill_file.name
            copy_static(skill_file, dest)
            written.append(dest.relative_to(target))

    # Git init + hooks install
    if init_git:
        git.init_repo(target)
        hooks_src = hooks_dir()
        for hook_name in ("pre-commit", "pre-push", "commit-msg", "post-merge"):
            hook_file = hooks_src / hook_name
            if hook_file.is_file():
                git.install_hook(hook_file, target)
        git.add_all(target)
        commit_msg = f"joinery: bench setup, tier={tier}"
        git.commit(target, commit_msg)

    return written


def _strip_template_suffix(filename: str) -> str:
    for suffix in (".template", ".starter", ".global"):
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    return filename


def _relative_all(target: Path, paths: list[Path]) -> list[Path]:
    """Convert a list of paths to target-relative if not already."""
    return [p if not p.is_absolute() else p.relative_to(target) for p in paths]


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

"""Tests for joinery.templates — rendering."""

from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

from joinery.templates import _strip_template_suffix, copy_template, render_context


def test_render_context_has_required_keys() -> None:
    ctx = render_context(project_name="x", tier="production", language="python")
    assert ctx["project_name"] == "x"
    assert ctx["tier"] == "production"
    assert ctx["language"] == "python"
    assert "init_at" in ctx
    assert "date" in ctx
    assert "joinery_version" in ctx


def test_copy_template_renders_placeholders(tmp_path: Path) -> None:
    src = tmp_path / "src.md.template"
    src.write_text("Project: {{project_name}}, tier: {{tier}}.\n", encoding="utf-8")
    target = tmp_path / "out.md"
    ctx = render_context(project_name="hello", tier="standard", language="python")
    copy_template(src, target, ctx)
    assert target.read_text(encoding="utf-8") == "Project: hello, tier: standard.\n"


def test_copy_template_raises_on_unknown_variable(tmp_path: Path) -> None:
    """Jinja2 StrictUndefined catches typos in template variables."""
    src = tmp_path / "src.md.template"
    src.write_text("Hello {{unknown_var}}!", encoding="utf-8")
    target = tmp_path / "out.md"
    ctx = render_context(project_name="x", tier="standard", language="python")
    with pytest.raises(jinja2.UndefinedError):
        copy_template(src, target, ctx)


def test_strip_template_suffix() -> None:
    assert _strip_template_suffix("plan.md.template") == "plan.md"
    assert _strip_template_suffix("CLAUDE.md.starter") == "CLAUDE.md"
    assert _strip_template_suffix("CLAUDE.md.global") == "CLAUDE.md"
    assert _strip_template_suffix("README.md") == "README.md"  # no suffix
    assert (
        _strip_template_suffix("framework.config.toml.production")
        == "framework.config.toml.production"
    )

"""Tests for joinery.lang — language detection."""

from __future__ import annotations

from pathlib import Path

from joinery.lang import detect_language, is_supported


def test_detect_python_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    assert detect_language(tmp_path) == "python"


def test_detect_python_from_py_file(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    assert detect_language(tmp_path) == "python"


def test_detect_typescript_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert detect_language(tmp_path) == "typescript"


def test_detect_typescript_from_tsconfig(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    assert detect_language(tmp_path) == "typescript"


def test_detect_polyglot_when_both(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert detect_language(tmp_path) == "polyglot"


def test_detect_none_when_empty(tmp_path: Path) -> None:
    assert detect_language(tmp_path) is None


def test_is_supported() -> None:
    assert is_supported("python")
    assert is_supported("typescript")
    assert is_supported("polyglot")
    assert not is_supported("rust")
    assert not is_supported("go")
    assert not is_supported("")

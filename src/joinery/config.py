"""framework.config.toml read/render helpers.

The workshop CLI reads tier-variant template files from templates/config/
and renders them with project-specific values at init time.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Literal

Tier = Literal["production", "standard", "sketch"]


def read_config(project_root: Path) -> dict[str, Any]:
    """Read .workshop/config.toml from a project root.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    config_path = project_root / ".workshop" / "config.toml"
    if not config_path.is_file():
        raise FileNotFoundError(
            f"No .workshop/config.toml at {project_root}. "
            f"This directory is not a Joinery project. Run `workshop init` first."
        )
    with config_path.open("rb") as f:
        return tomllib.load(f)


def get_tier(config: dict[str, Any]) -> Tier:
    tier = config.get("meta", {}).get("tier", "standard")
    if tier == "production":
        return "production"
    if tier == "standard":
        return "standard"
    if tier == "sketch":
        return "sketch"
    raise ValueError(f"Invalid tier in config: {tier!r}")


def get_primary_language(config: dict[str, Any]) -> str:
    value = config.get("lang", {}).get("primary", "python")
    return str(value)

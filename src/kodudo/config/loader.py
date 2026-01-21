"""Configuration loader for kodudo."""

from pathlib import Path
from typing import Any

import yaml

from kodudo.config.types import Config
from kodudo.errors import ConfigError


def load_config(path: str | Path) -> Config:
    """Load and validate a kodudo config file.

    Args:
        path: Path to YAML config file

    Returns:
        Validated Config object

    Raises:
        ConfigError: If config file cannot be read or is invalid
    """
    path = Path(path)

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read config file: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML mapping")

    return _parse_config(raw, base_path=path.parent)


def _parse_config(raw: dict[str, Any], base_path: Path) -> Config:
    """Parse raw config dict into Config object.

    Args:
        raw: Raw config dictionary
        base_path: Base path for resolving relative paths

    Returns:
        Config object

    Raises:
        ConfigError: If required fields are missing or invalid
    """
    # Required fields
    if "input" not in raw:
        raise ConfigError("Config must have 'input' field")
    if "template" not in raw:
        raise ConfigError("Config must have 'template' field")
    if "output" not in raw:
        raise ConfigError("Config must have 'output' field")

    # Parse template_dirs
    template_dirs_raw = raw.get("template_dirs", [])
    if not isinstance(template_dirs_raw, list):
        raise ConfigError("'template_dirs' must be a list")
    template_dirs = tuple(Path(p) for p in template_dirs_raw)

    # Parse format
    format_value = raw.get("format")
    if format_value is not None and format_value not in ("html", "markdown", "text"):
        raise ConfigError(f"Invalid format: {format_value}. Must be html, markdown, or text")

    # Parse context (inline dict in config)
    context = raw.get("context")
    if context is not None and not isinstance(context, dict):
        raise ConfigError("'context' must be a mapping")

    return Config(
        input=Path(raw["input"]),
        template=Path(raw["template"]),
        output=Path(raw["output"]),
        format=format_value,
        template_dirs=template_dirs,
        context_file=Path(raw["context_file"]) if raw.get("context_file") else None,
        context=context,
        base_path=base_path,
    )

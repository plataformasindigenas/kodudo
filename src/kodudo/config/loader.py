"""Configuration loader for kodudo."""

from pathlib import Path
from typing import Any

import yaml

from kodudo.config.expander import BatchConfig, OutputSpec
from kodudo.config.types import Config
from kodudo.errors import ConfigError

_RESERVED_FOREACH_NAMES = frozenset({"data", "meta", "config"})


def load_config(path: str | Path) -> BatchConfig:
    """Load and validate a kodudo config file.

    Args:
        path: Path to YAML config file

    Returns:
        Validated BatchConfig object

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


def _parse_config(raw: dict[str, Any], base_path: Path) -> BatchConfig:
    """Parse raw config dict into BatchConfig object.

    Args:
        raw: Raw config dictionary
        base_path: Base path for resolving relative paths

    Returns:
        BatchConfig object

    Raises:
        ConfigError: If required fields are missing or invalid
    """
    # Required fields
    if "input" not in raw:
        raise ConfigError("Config must have 'input' field")
    if "template" not in raw:
        raise ConfigError("Config must have 'template' field")

    # output vs outputs: mutually exclusive
    has_output = "output" in raw
    has_outputs = "outputs" in raw

    if has_output and has_outputs:
        raise ConfigError("'output' and 'outputs' are mutually exclusive")
    if not has_output and not has_outputs:
        raise ConfigError("Config must have 'output' or 'outputs' field")

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

    # Parse foreach
    foreach = raw.get("foreach")
    if foreach is not None:
        if not isinstance(foreach, str):
            raise ConfigError("'foreach' must be a string")
        if foreach in _RESERVED_FOREACH_NAMES:
            raise ConfigError(
                f"'foreach' variable name '{foreach}' is reserved. "
                f"Cannot use: {', '.join(sorted(_RESERVED_FOREACH_NAMES))}"
            )

    # Parse outputs
    output_specs: tuple[OutputSpec, ...] | None = None
    if has_outputs:
        output_specs = _parse_outputs(raw["outputs"])

    # Determine output path
    output_path = Path(raw["output"]) if has_output else Path(".")

    config = Config(
        input=Path(raw["input"]),
        template=Path(raw["template"]),
        output=output_path,
        format=format_value,
        template_dirs=template_dirs,
        context_file=Path(raw["context_file"]) if raw.get("context_file") else None,
        context=context,
        base_path=base_path,
        foreach=foreach,
    )

    return BatchConfig(config=config, outputs=output_specs)


def _parse_outputs(raw_outputs: Any) -> tuple[OutputSpec, ...]:
    """Parse the outputs list from config.

    Args:
        raw_outputs: Raw outputs value from config

    Returns:
        Tuple of OutputSpec objects

    Raises:
        ConfigError: If outputs format is invalid
    """
    if not isinstance(raw_outputs, list):
        raise ConfigError("'outputs' must be a list")

    specs: list[OutputSpec] = []
    for i, entry in enumerate(raw_outputs):
        if not isinstance(entry, dict):
            raise ConfigError(f"outputs[{i}] must be a mapping")
        if "output" not in entry:
            raise ConfigError(f"outputs[{i}] must have 'output' field")

        # Parse template_dirs if present
        td = entry.get("template_dirs")
        template_dirs: tuple[str, ...] | None = None
        if td is not None:
            if not isinstance(td, list):
                raise ConfigError(f"outputs[{i}].template_dirs must be a list")
            template_dirs = tuple(td)

        # Parse context if present
        ctx = entry.get("context")
        if ctx is not None and not isinstance(ctx, dict):
            raise ConfigError(f"outputs[{i}].context must be a mapping")

        specs.append(
            OutputSpec(
                output=entry["output"],
                input=entry.get("input"),
                template=entry.get("template"),
                format=entry.get("format"),
                template_dirs=template_dirs,
                context_file=entry.get("context_file"),
                context=ctx,
            )
        )

    return tuple(specs)

"""Config expansion for multi-output and foreach rendering."""

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from kodudo.config.types import Config
from kodudo.errors import ConfigError


@dataclass(frozen=True)
class OutputSpec:
    """One entry in the outputs list.

    All fields optional except output. When present, they override
    the corresponding field in the base Config.
    """

    output: str
    input: str | None = None
    template: str | None = None
    format: str | None = None
    template_dirs: tuple[str, ...] | None = None
    context_file: str | None = None
    context: dict[str, Any] | None = None


@dataclass(frozen=True)
class BatchConfig:
    """Wraps a Config with optional multi-output specs.

    Attributes:
        config: The base Config object
        outputs: Optional tuple of OutputSpec for multi-output rendering
    """

    config: Config
    outputs: tuple[OutputSpec, ...] | None = None


def interpolate_path(path_str: str, variables: dict[str, Any]) -> str:
    """Resolve {var.field.subfield} placeholders in a path string.

    Args:
        path_str: Path string with optional {var.field} placeholders
        variables: Dictionary of variable values for interpolation

    Returns:
        Interpolated path string

    Raises:
        ConfigError: If a placeholder references a missing key
    """

    def _resolve(match: re.Match[str]) -> str:
        expr = match.group(1)
        parts = expr.split(".")
        current: Any = variables
        for part in parts:
            if not isinstance(current, dict):
                raise ConfigError(
                    f"Cannot resolve '{expr}': '{part}' is not a key "
                    f"in a non-mapping value"
                )
            if part not in current:
                raise ConfigError(
                    f"Cannot resolve '{expr}': key '{part}' not found"
                )
            current = current[part]
        return str(current)

    return re.sub(r"\{([^}]+)\}", _resolve, path_str)


def expand_config(
    config: Config,
    outputs: tuple[OutputSpec, ...] | None = None,
    data: tuple[dict[str, Any], ...] | None = None,
) -> list[Config]:
    """Expand a config into multiple concrete configs.

    Handles three cases:
    1. No outputs and no foreach: returns [config]
    2. outputs only: one Config per OutputSpec
    3. foreach only: one Config per data record
    4. Both: Cartesian product (outputs x foreach)

    Args:
        config: Base Config object
        outputs: Optional output specs for multi-output
        data: Data records for foreach expansion

    Returns:
        List of concrete Config instances ready for rendering

    Raises:
        ConfigError: If foreach is set but no data is provided
    """
    has_outputs = outputs is not None and len(outputs) > 0
    has_foreach = config.foreach is not None

    if not has_outputs and not has_foreach:
        return [config]

    # Build base configs from outputs (or just the original)
    base_configs: list[Config]
    if has_outputs:
        assert outputs is not None
        base_configs = [_apply_output_spec(config, spec) for spec in outputs]
    else:
        base_configs = [config]

    if not has_foreach:
        return base_configs

    # foreach expansion
    assert config.foreach is not None
    if data is None:
        raise ConfigError("foreach requires data but none was provided")

    if len(data) == 0:
        return []

    expanded: list[Config] = []
    for base in base_configs:
        for record in data:
            variables = {config.foreach: record}
            new_output = interpolate_path(str(base.output), variables)

            # Inject loop variable into context
            merged_context = dict(base.context or {})
            merged_context[config.foreach] = record

            expanded.append(
                replace(
                    base,
                    output=Path(new_output),
                    context=merged_context,
                )
            )

    return expanded


def _apply_output_spec(config: Config, spec: OutputSpec) -> Config:
    """Create a new Config by applying an OutputSpec's overrides.

    Context is shallow-merged: parent context + spec context, spec wins.
    """
    overrides: dict[str, Any] = {"output": Path(spec.output)}

    if spec.input is not None:
        overrides["input"] = Path(spec.input)
    if spec.template is not None:
        overrides["template"] = Path(spec.template)
    if spec.format is not None:
        overrides["format"] = spec.format
    if spec.template_dirs is not None:
        overrides["template_dirs"] = tuple(Path(p) for p in spec.template_dirs)
    if spec.context_file is not None:
        overrides["context_file"] = Path(spec.context_file)

    # Shallow-merge context: parent + spec, spec wins
    if spec.context is not None:
        merged = dict(config.context or {})
        merged.update(spec.context)
        overrides["context"] = merged

    return replace(config, **overrides)

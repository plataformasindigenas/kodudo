"""Kodudo - Cook your data into documents.

Kodudo takes validated data from aptoro and renders it through Jinja2
templates to produce outputs like HTML, Markdown, and plain text.

Example:
    >>> import kodudo
    >>>
    >>> # From config file
    >>> kodudo.cook("config.yaml")
    >>>
    >>> # Programmatic usage
    >>> result = kodudo.render(
    ...     data=[{"name": "Item 1"}, {"name": "Item 2"}],
    ...     template="templates/list.html.j2",
    ... )
"""

from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from kodudo.config import (
    BatchConfig,
    Config,
    OutputSpec,
    expand_config,
    interpolate_path,
    load_config,
)
from kodudo.data import LoadedData, load_data
from kodudo.errors import ConfigError, DataError, KodudoError, RenderError
from kodudo.rendering import create_environment
from kodudo.rendering import render as _render

__version__ = "0.2.0"

__all__ = [
    # Main functions
    "cook",
    "cook_from_config",
    "render",
    # Loaders
    "load_config",
    "load_data",
    # Types
    "BatchConfig",
    "Config",
    "LoadedData",
    "OutputSpec",
    # Expansion
    "expand_config",
    "interpolate_path",
    # Errors
    "KodudoError",
    "ConfigError",
    "DataError",
    "RenderError",
]


def cook(config_path: str | Path) -> list[Path]:
    """Cook data according to a config file.

    Loads config, data, renders template, writes output.

    Args:
        config_path: Path to YAML config file

    Returns:
        List of output file paths

    Raises:
        ConfigError: If config is invalid
        DataError: If data cannot be loaded
        RenderError: If template rendering fails
    """
    batch = load_config(config_path)
    return cook_from_config(batch.config, outputs=batch.outputs)


def cook_from_config(
    config: Config,
    *,
    outputs: tuple[OutputSpec, ...] | None = None,
    context: dict[str, Any] | None = None,
    output: str | Path | None = None,
) -> list[Path]:
    """Cook data using a Config object.

    Args:
        config: Configuration object
        outputs: Optional output specs for multi-output rendering
        context: Optional context overrides (merged on top of config context)
        output: Optional output path override

    Returns:
        List of output file paths

    Raises:
        DataError: If data cannot be loaded
        RenderError: If template rendering fails
    """
    # Apply call-site overrides
    if context is not None or output is not None:
        overrides: dict[str, Any] = {}
        if output is not None:
            overrides["output"] = Path(output)
        if context is not None:
            merged = dict(config.context or {})
            merged.update(context)
            overrides["context"] = merged
        config = replace(config, **overrides)

    # Load data once
    loaded = load_data(config.resolved_input)

    # Expand config into concrete instances
    expanded = expand_config(config, outputs=outputs, data=loaded.raw)

    result_paths: list[Path] = []
    for cfg in expanded:
        output_path = _cook_single(cfg, loaded)
        result_paths.append(output_path)

    return result_paths


def _cook_single(config: Config, loaded: LoadedData) -> Path:
    """Cook a single concrete config with pre-loaded data.

    Args:
        config: Concrete single-output Config
        loaded: Pre-loaded data

    Returns:
        Path to the output file
    """
    # Merge context from file and inline
    context: dict[str, Any] = {}
    if config.resolved_context_file:
        context = _load_context_file(config.resolved_context_file)
    if config.context:
        context.update(config.context)

    # Setup Jinja2 environment
    template_path = config.resolved_template
    template_dirs = (template_path.parent,) + config.resolved_template_dirs
    env = create_environment(template_dirs)

    # Build config dict for template
    config_dict = {
        "input": str(config.resolved_input),
        "output": str(config.resolved_output),
        "format": config.get_format(),
    }

    # Render
    result = _render(
        env,
        template_path.name,
        data=loaded.raw,
        meta=loaded.meta,
        config=config_dict,
        context=context,
    )

    # Write output
    output_path = config.resolved_output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")

    return output_path


def render(
    data: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    template: str | Path,
    *,
    meta: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    template_dirs: tuple[Path, ...] = (),
) -> str:
    """Render a template with data (programmatic API).

    Args:
        data: List of record dictionaries
        template: Path to Jinja2 template
        meta: Optional schema metadata dictionary
        context: Optional additional template variables
        template_dirs: Additional template search paths

    Returns:
        Rendered template string

    Raises:
        RenderError: If template rendering fails
    """
    template = Path(template)
    dirs = (template.parent,) + template_dirs
    env = create_environment(dirs)

    return _render(
        env,
        template.name,
        data=tuple(data),
        meta=meta or {},
        config={},
        context=context,
    )


def _load_context_file(path: Path) -> dict[str, Any]:
    """Load context from a YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary of context variables

    Raises:
        ConfigError: If file cannot be read or is invalid
    """
    if not path.exists():
        raise ConfigError(f"Context file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in context file: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read context file: {e}") from e

    if content is None:
        return {}

    if not isinstance(content, dict):
        raise ConfigError("Context file must contain a YAML mapping")

    return content

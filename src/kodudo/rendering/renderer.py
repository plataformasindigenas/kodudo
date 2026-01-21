"""Template renderer for kodudo."""

from typing import Any

from jinja2 import Environment, TemplateNotFound, TemplateSyntaxError, UndefinedError

from kodudo.errors import RenderError


def render(
    env: Environment,
    template_name: str,
    *,
    data: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    meta: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> str:
    """Render a template with the given data.

    Template receives these variables:
    - data: List of record dictionaries
    - meta: Schema metadata dictionary (empty if no metadata)
    - config: Configuration values dictionary
    - ...context: Any extra variables from context/context_file

    Args:
        env: Jinja2 environment
        template_name: Name of template to render
        data: List of record dictionaries
        meta: Schema metadata dictionary
        config: Configuration values dictionary
        context: Additional template variables

    Returns:
        Rendered template string

    Raises:
        RenderError: If template not found or rendering fails
    """
    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise RenderError(f"Template not found: {template_name}") from e
    except TemplateSyntaxError as e:
        raise RenderError(f"Template syntax error in {e.filename}:{e.lineno}: {e.message}") from e

    template_vars: dict[str, Any] = {
        "data": list(data),  # Convert tuple to list for template iteration
        "meta": meta,
        "config": config,
    }

    if context:
        template_vars.update(context)

    try:
        return template.render(**template_vars)
    except UndefinedError as e:
        raise RenderError(f"Undefined variable in template: {e}") from e
    except Exception as e:
        raise RenderError(f"Render failed: {e}") from e

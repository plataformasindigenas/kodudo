"""Jinja2 environment factory for kodudo."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def create_environment(
    template_dirs: tuple[Path, ...] = (),
    autoescape_for: tuple[str, ...] = ("html", "xml"),
) -> Environment:
    """Create a Jinja2 environment with the given template directories.

    Uses pure Jinja2 without custom filters (YAGNI principle).

    Args:
        template_dirs: Directories to search for templates
        autoescape_for: File extensions to autoescape (for HTML safety)

    Returns:
        Configured Jinja2 Environment
    """
    # Default to current directory if no dirs specified
    search_paths = [str(p) for p in template_dirs] if template_dirs else ["."]

    loader = FileSystemLoader(search_paths)

    env = Environment(
        loader=loader,
        autoescape=select_autoescape(autoescape_for),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    return env

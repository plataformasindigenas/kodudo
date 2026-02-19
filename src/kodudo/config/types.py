"""Configuration types for kodudo."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    """Kodudo rendering configuration.

    Attributes:
        input: Path to JSON data file (with aptoro metadata)
        template: Path to main Jinja2 template
        output: Output file path
        format: Output format (html, markdown, text), inferred from template if not set
        template_dirs: Additional template search paths
        context_file: Path to external YAML context file
        context: Inline context variables from config
        base_path: Base path for resolving relative paths
    """

    input: Path
    template: Path
    output: Path
    format: str | None = None
    template_dirs: tuple[Path, ...] = ()
    context_file: Path | None = None
    context: dict[str, Any] | None = None
    base_path: Path | None = None
    foreach: str | None = None

    def get_format(self) -> str:
        """Return format, inferring from template extension if needed."""
        if self.format:
            return self.format

        # Check template stem for format hint: fauna_list.html.j2 -> html
        stem = self.template.stem
        if stem.endswith(".html"):
            return "html"
        if stem.endswith(".md"):
            return "markdown"
        return "text"

    def resolve_path(self, path: Path) -> Path:
        """Resolve a path relative to base_path if not absolute."""
        if path.is_absolute():
            return path
        if self.base_path:
            return self.base_path / path
        return path

    @property
    def resolved_input(self) -> Path:
        """Get resolved input path."""
        return self.resolve_path(self.input)

    @property
    def resolved_template(self) -> Path:
        """Get resolved template path."""
        return self.resolve_path(self.template)

    @property
    def resolved_output(self) -> Path:
        """Get resolved output path."""
        return self.resolve_path(self.output)

    @property
    def resolved_context_file(self) -> Path | None:
        """Get resolved context file path."""
        if self.context_file:
            return self.resolve_path(self.context_file)
        return None

    @property
    def resolved_template_dirs(self) -> tuple[Path, ...]:
        """Get resolved template directories."""
        return tuple(self.resolve_path(p) for p in self.template_dirs)

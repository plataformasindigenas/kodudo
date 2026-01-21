from pathlib import Path

import pytest

from kodudo.errors import RenderError
from kodudo.rendering.engine import create_environment
from kodudo.rendering.renderer import render


def test_render_basic(tmp_path: Path) -> None:
    """Test basic variable rendering."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "hello.j2").write_text("Hello {{ name }}!", encoding="utf-8")

    env = create_environment((template_dir,))
    result = render(env, "hello.j2", data=[], meta={}, config={}, context={"name": "World"})
    assert result == "Hello World!"


def test_render_data_access(tmp_path: Path) -> None:
    """Test iterating over data list."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "list.j2").write_text(
        "{% for item in data %}{{ item.name }}\n{% endfor %}", encoding="utf-8"
    )

    env = create_environment((template_dir,))
    result = render(
        env,
        "list.j2",
        data=[{"name": "A"}, {"name": "B"}],
        meta={},
        config={},
        context={},
    )
    assert result == "A\nB\n"


def test_render_meta_config_access(tmp_path: Path) -> None:
    """Test access to meta and config variables."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "info.j2").write_text(
        "Meta: {{ meta.version }}, Output: {{ config.output }}", encoding="utf-8"
    )

    env = create_environment((template_dir,))
    result = render(
        env,
        "info.j2",
        data=[],
        meta={"version": "1.0"},
        config={"output": "out.txt"},
        context={},
    )
    assert result == "Meta: 1.0, Output: out.txt"


def test_render_template_not_found(tmp_path: Path) -> None:
    """Test error when template is missing."""
    env = create_environment((tmp_path,))
    with pytest.raises(RenderError, match="Template not found"):
        render(env, "missing.j2", data=[], meta={}, config={})


def test_render_syntax_error(tmp_path: Path) -> None:
    """Test error on invalid template syntax."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "bad.j2").write_text("{% for %}", encoding="utf-8")

    env = create_environment((template_dir,))
    with pytest.raises(RenderError, match="Template syntax error"):
        render(env, "bad.j2", data=[], meta={}, config={})

"""Tests for config expansion and interpolation."""

from pathlib import Path

import pytest

from kodudo.config.expander import OutputSpec, expand_config, interpolate_path
from kodudo.config.types import Config
from kodudo.errors import ConfigError


def _make_config(**overrides: object) -> Config:
    """Create a Config with sensible defaults."""
    defaults = {
        "input": Path("data.json"),
        "template": Path("template.html.j2"),
        "output": Path("output.html"),
        "base_path": Path("/project"),
    }
    defaults.update(overrides)
    return Config(**defaults)  # type: ignore[arg-type]


class TestInterpolatePath:
    def test_simple_variable(self) -> None:
        result = interpolate_path("{name}.html", {"name": "hello"})
        assert result == "hello.html"

    def test_nested_variable(self) -> None:
        result = interpolate_path(
            "{article.slug}.html", {"article": {"slug": "my-post"}}
        )
        assert result == "my-post.html"

    def test_multiple_placeholders(self) -> None:
        result = interpolate_path(
            "{lang}/{article.slug}.html",
            {"lang": "en", "article": {"slug": "hello"}},
        )
        assert result == "en/hello.html"

    def test_no_placeholders(self) -> None:
        result = interpolate_path("output.html", {"name": "test"})
        assert result == "output.html"

    def test_missing_key_raises(self) -> None:
        with pytest.raises(ConfigError, match="not found"):
            interpolate_path("{missing}.html", {"name": "test"})

    def test_non_mapping_intermediate_raises(self) -> None:
        with pytest.raises(ConfigError, match="non-mapping"):
            interpolate_path("{article.slug}.html", {"article": "not-a-dict"})


class TestExpandConfig:
    def test_single_output_passthrough(self) -> None:
        config = _make_config()
        result = expand_config(config)
        assert result == [config]

    def test_outputs_only(self) -> None:
        config = _make_config(output=Path("."))
        specs = (
            OutputSpec(output="en/index.html", context={"lang": "en"}),
            OutputSpec(output="pt/index.html", context={"lang": "pt"}),
        )
        result = expand_config(config, outputs=specs)

        assert len(result) == 2
        assert result[0].output == Path("en/index.html")
        assert result[0].context == {"lang": "en"}
        assert result[1].output == Path("pt/index.html")
        assert result[1].context == {"lang": "pt"}

    def test_context_merging(self) -> None:
        config = _make_config(context={"site": "mysite", "lang": "default"})
        specs = (OutputSpec(output="out.html", context={"lang": "en"}),)
        result = expand_config(config, outputs=specs)

        assert result[0].context == {"site": "mysite", "lang": "en"}

    def test_foreach_only(self) -> None:
        config = _make_config(
            output=Path("{article.slug}.html"), foreach="article"
        )
        data = (
            {"slug": "hello", "title": "Hello"},
            {"slug": "bye", "title": "Bye"},
        )
        result = expand_config(config, data=data)

        assert len(result) == 2
        assert result[0].output == Path("hello.html")
        assert result[0].context == {"article": {"slug": "hello", "title": "Hello"}}
        assert result[1].output == Path("bye.html")
        assert result[1].context == {"article": {"slug": "bye", "title": "Bye"}}

    def test_foreach_injects_into_context(self) -> None:
        config = _make_config(
            output=Path("{item.id}.html"),
            foreach="item",
            context={"base_url": "/site"},
        )
        data = ({"id": "1", "name": "One"},)
        result = expand_config(config, data=data)

        assert result[0].context == {
            "base_url": "/site",
            "item": {"id": "1", "name": "One"},
        }

    def test_foreach_empty_data(self) -> None:
        config = _make_config(
            output=Path("{article.slug}.html"), foreach="article"
        )
        result = expand_config(config, data=())
        assert result == []

    def test_foreach_without_data_raises(self) -> None:
        config = _make_config(
            output=Path("{article.slug}.html"), foreach="article"
        )
        with pytest.raises(ConfigError, match="foreach requires data"):
            expand_config(config)

    def test_cartesian_product(self) -> None:
        config = _make_config(foreach="article")
        specs = (
            OutputSpec(output="en/{article.slug}.html", context={"lang": "en"}),
            OutputSpec(output="pt/{article.slug}.html", context={"lang": "pt"}),
        )
        data = (
            {"slug": "hello", "title": "Hello"},
            {"slug": "bye", "title": "Bye"},
        )
        result = expand_config(config, outputs=specs, data=data)

        assert len(result) == 4
        # en/hello, en/bye, pt/hello, pt/bye
        assert result[0].output == Path("en/hello.html")
        assert result[0].context == {"lang": "en", "article": {"slug": "hello", "title": "Hello"}}
        assert result[1].output == Path("en/bye.html")
        assert result[1].context == {"lang": "en", "article": {"slug": "bye", "title": "Bye"}}
        assert result[2].output == Path("pt/hello.html")
        assert result[2].context == {"lang": "pt", "article": {"slug": "hello", "title": "Hello"}}
        assert result[3].output == Path("pt/bye.html")
        assert result[3].context == {"lang": "pt", "article": {"slug": "bye", "title": "Bye"}}

    def test_output_spec_overrides_template(self) -> None:
        config = _make_config(output=Path("."))
        specs = (
            OutputSpec(output="out.html", template="other.html.j2"),
        )
        result = expand_config(config, outputs=specs)

        assert result[0].template == Path("other.html.j2")
        assert result[0].output == Path("out.html")

    def test_output_spec_overrides_input(self) -> None:
        config = _make_config(output=Path("."))
        specs = (
            OutputSpec(output="out.html", input="other.json"),
        )
        result = expand_config(config, outputs=specs)

        assert result[0].input == Path("other.json")

    def test_output_spec_overrides_format(self) -> None:
        config = _make_config(output=Path("."))
        specs = (
            OutputSpec(output="out.md", format="markdown"),
        )
        result = expand_config(config, outputs=specs)

        assert result[0].format == "markdown"

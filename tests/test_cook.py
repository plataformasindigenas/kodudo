import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from kodudo import cook, cook_from_config, load_config
from kodudo.errors import KodudoError


def test_cook_full_flow(tmp_path: Path) -> None:
    """Test full rendering flow from config file."""
    # Setup files
    data: list[dict[str, Any]] = [{"name": "Test"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("<h1>{{ data[0].name }}</h1>", encoding="utf-8")

    output_file = tmp_path / "output.html"

    config_data = {
        "input": str(data_file.name),  # Relative path test
        "template": str(template_file.name),
        "output": str(output_file.name),
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Run cook
    result_paths = cook(config_file)

    assert result_paths == [output_file]
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "<h1>Test</h1>"


def test_cook_with_context_file(tmp_path: Path) -> None:
    """Test rendering with external context file."""
    data: list[dict[str, Any]] = []
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.txt"
    template_file.write_text("{{ title }}", encoding="utf-8")

    context_file = tmp_path / "context.yaml"
    with open(context_file, "w") as f:
        yaml.dump({"title": "My Title"}, f)

    output_file = tmp_path / "output.txt"

    config_data = {
        "input": str(data_file),
        "template": str(template_file),
        "output": str(output_file),
        "context_file": str(context_file),
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    cook(config_file)
    assert output_file.read_text(encoding="utf-8") == "My Title"


def test_cook_error_propagation(tmp_path: Path) -> None:
    """Test that errors are propagated as KodudoError."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("invalid: : yaml", encoding="utf-8")

    with pytest.raises(KodudoError):
        cook(config_file)


def test_cook_missing_context_file(tmp_path: Path) -> None:
    """Test error when context file is missing."""
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump([], f)

    template_file = tmp_path / "t.j2"
    template_file.write_text("x")

    config_data = {
        "input": str(data_file),
        "template": str(template_file),
        "output": "out.txt",
        "context_file": "missing.yaml",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(KodudoError, match="Context file not found"):
        cook(config_file)


def test_cook_outputs_list(tmp_path: Path) -> None:
    """Test cooking with multiple outputs."""
    data: list[dict[str, Any]] = [{"name": "Test"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("{{ lang }}: {{ data[0].name }}", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "outputs": [
            {"output": "en/index.html", "context": {"lang": "en"}},
            {"output": "pt/index.html", "context": {"lang": "pt"}},
        ],
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result_paths = cook(config_file)

    assert len(result_paths) == 2
    assert result_paths[0] == tmp_path / "en" / "index.html"
    assert result_paths[1] == tmp_path / "pt" / "index.html"
    assert result_paths[0].read_text(encoding="utf-8") == "en: Test"
    assert result_paths[1].read_text(encoding="utf-8") == "pt: Test"


def test_cook_foreach(tmp_path: Path) -> None:
    """Test cooking with foreach (per-record rendering)."""
    data: list[dict[str, Any]] = [
        {"slug": "hello", "title": "Hello World"},
        {"slug": "bye", "title": "Goodbye"},
    ]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "article.html.j2"
    template_file.write_text("<h1>{{ article.title }}</h1>", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "{article.slug}.html",
        "foreach": "article",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result_paths = cook(config_file)

    assert len(result_paths) == 2
    assert result_paths[0] == tmp_path / "hello.html"
    assert result_paths[1] == tmp_path / "bye.html"
    assert result_paths[0].read_text(encoding="utf-8") == "<h1>Hello World</h1>"
    assert result_paths[1].read_text(encoding="utf-8") == "<h1>Goodbye</h1>"


def test_cook_foreach_empty_data(tmp_path: Path) -> None:
    """Test foreach with empty data produces no outputs."""
    data: list[dict[str, Any]] = []
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "article.html.j2"
    template_file.write_text("<h1>{{ article.title }}</h1>", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "{article.slug}.html",
        "foreach": "article",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result_paths = cook(config_file)
    assert result_paths == []


def test_cook_foreach_x_outputs(tmp_path: Path) -> None:
    """Test Cartesian product of outputs x foreach."""
    data: list[dict[str, Any]] = [
        {"slug": "hello", "title": "Hello"},
        {"slug": "bye", "title": "Bye"},
    ]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "article.html.j2"
    template_file.write_text(
        "{{ lang }}: {{ article.title }}", encoding="utf-8"
    )

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "outputs": [
            {"output": "en/{article.slug}.html", "context": {"lang": "en"}},
            {"output": "pt/{article.slug}.html", "context": {"lang": "pt"}},
        ],
        "foreach": "article",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    result_paths = cook(config_file)

    assert len(result_paths) == 4
    assert (tmp_path / "en" / "hello.html").read_text(encoding="utf-8") == "en: Hello"
    assert (tmp_path / "en" / "bye.html").read_text(encoding="utf-8") == "en: Bye"
    assert (tmp_path / "pt" / "hello.html").read_text(encoding="utf-8") == "pt: Hello"
    assert (tmp_path / "pt" / "bye.html").read_text(encoding="utf-8") == "pt: Bye"


def test_cook_from_config_context_override(tmp_path: Path) -> None:
    """Test cook_from_config with context override."""
    data: list[dict[str, Any]] = [{"name": "Test"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("{{ lang }}: {{ data[0].name }}", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "output.html",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)
    result_paths = cook_from_config(batch.config, context={"lang": "en"})

    assert result_paths == [tmp_path / "output.html"]
    assert (tmp_path / "output.html").read_text(encoding="utf-8") == "en: Test"


def test_cook_from_config_output_override(tmp_path: Path) -> None:
    """Test cook_from_config with output path override."""
    data: list[dict[str, Any]] = [{"name": "Test"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("<h1>{{ data[0].name }}</h1>", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "original.html",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)
    result_paths = cook_from_config(batch.config, output="overridden.html")

    assert result_paths == [tmp_path / "overridden.html"]
    assert (tmp_path / "overridden.html").read_text(encoding="utf-8") == "<h1>Test</h1>"
    assert not (tmp_path / "original.html").exists()


def test_cook_from_config_context_merges_with_config(tmp_path: Path) -> None:
    """Test that context override merges with config context."""
    data: list[dict[str, Any]] = []
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("{{ site }} {{ lang }}", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "output.html",
        "context": {"site": "mysite", "lang": "default"},
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)
    # Override lang, keep site from config
    cook_from_config(batch.config, context={"lang": "pt"})

    assert (tmp_path / "output.html").read_text(encoding="utf-8") == "mysite pt"


def test_cook_from_config_context_and_output_override(tmp_path: Path) -> None:
    """Test cook_from_config with both context and output overrides."""
    data: list[dict[str, Any]] = [{"name": "Test"}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    template_file = tmp_path / "template.html.j2"
    template_file.write_text("{{ lang }}: {{ data[0].name }}", encoding="utf-8")

    config_data = {
        "input": str(data_file.name),
        "template": str(template_file.name),
        "output": "original.html",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)

    # Simulate the locale loop pattern from the suggestion
    for locale in ("pt", "en"):
        cook_from_config(
            batch.config,
            context={"lang": locale},
            output=f"docs/{locale}/fauna.html",
        )

    assert (tmp_path / "docs" / "pt" / "fauna.html").read_text(encoding="utf-8") == "pt: Test"
    assert (tmp_path / "docs" / "en" / "fauna.html").read_text(encoding="utf-8") == "en: Test"

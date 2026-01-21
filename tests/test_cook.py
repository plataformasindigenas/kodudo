import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from kodudo import cook
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
    result_path = cook(config_file)

    assert result_path == output_file
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

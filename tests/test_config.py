from pathlib import Path

import pytest
import yaml

from kodudo.config.loader import load_config
from kodudo.errors import ConfigError


def test_load_config_valid(tmp_path: Path) -> None:
    """Test loading a valid configuration file."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "output.html",
        "template_dirs": ["templates"],
        "context": {"foo": "bar"},
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_file)

    assert config.input == Path("data.json")
    assert config.template == Path("template.html.j2")
    assert config.output == Path("output.html")
    assert config.context == {"foo": "bar"}
    assert config.template_dirs == (Path("templates"),)

    # Check path resolution relative to config file location
    assert config.resolved_input == tmp_path / "data.json"
    assert config.resolved_template == tmp_path / "template.html.j2"


def test_load_config_missing_field(tmp_path: Path) -> None:
    """Test that missing required fields raise ConfigError."""
    config_data = {
        "input": "data.json",
        # Missing template
        "output": "output.html",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="must have 'template' field"):
        load_config(config_file)


def test_load_config_file_not_found() -> None:
    """Test that a non-existent config file raises ConfigError."""
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config("non_existent.yaml")


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """Test that invalid YAML content raises ConfigError."""
    config_file = tmp_path / "bad_config.yaml"
    config_file.write_text("key: : value", encoding="utf-8")

    with pytest.raises(ConfigError, match="Invalid YAML"):
        load_config(config_file)


def test_get_format_inference(tmp_path: Path) -> None:
    """Test output format inference from template extension."""
    config_data = {
        "input": "data.json",
        "template": "template.md.j2",
        "output": "output.md",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_file)
    assert config.get_format() == "markdown"


def test_explicit_format(tmp_path: Path) -> None:
    """Test that explicit format overrides inference."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "output.txt",
        "format": "text",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    config = load_config(config_file)
    assert config.get_format() == "text"

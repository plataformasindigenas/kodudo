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

    batch = load_config(config_file)
    config = batch.config

    assert config.input == Path("data.json")
    assert config.template == Path("template.html.j2")
    assert config.output == Path("output.html")
    assert config.context == {"foo": "bar"}
    assert config.template_dirs == (Path("templates"),)
    assert batch.outputs is None

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

    batch = load_config(config_file)
    assert batch.config.get_format() == "markdown"


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

    batch = load_config(config_file)
    assert batch.config.get_format() == "text"


def test_load_config_with_outputs(tmp_path: Path) -> None:
    """Test loading config with outputs list."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "outputs": [
            {"output": "en/index.html", "context": {"lang": "en"}},
            {"output": "pt/index.html", "context": {"lang": "pt"}},
        ],
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)
    assert batch.outputs is not None
    assert len(batch.outputs) == 2
    assert batch.outputs[0].output == "en/index.html"
    assert batch.outputs[0].context == {"lang": "en"}
    assert batch.outputs[1].output == "pt/index.html"
    assert batch.outputs[1].context == {"lang": "pt"}


def test_load_config_output_and_outputs_exclusive(tmp_path: Path) -> None:
    """Test that output and outputs cannot both be present."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "out.html",
        "outputs": [{"output": "other.html"}],
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="mutually exclusive"):
        load_config(config_file)


def test_load_config_no_output_or_outputs(tmp_path: Path) -> None:
    """Test that at least output or outputs must be present."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="'output' or 'outputs'"):
        load_config(config_file)


def test_load_config_with_foreach(tmp_path: Path) -> None:
    """Test loading config with foreach field."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "output/{article.slug}.html",
        "foreach": "article",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    batch = load_config(config_file)
    assert batch.config.foreach == "article"


def test_load_config_foreach_not_string(tmp_path: Path) -> None:
    """Test that foreach must be a string."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "output.html",
        "foreach": 42,
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="'foreach' must be a string"):
        load_config(config_file)


def test_load_config_foreach_reserved_name(tmp_path: Path) -> None:
    """Test that foreach cannot use reserved variable names."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "output": "output.html",
        "foreach": "data",
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="reserved"):
        load_config(config_file)


def test_load_config_outputs_entry_missing_output(tmp_path: Path) -> None:
    """Test that each outputs entry must have output field."""
    config_data = {
        "input": "data.json",
        "template": "template.html.j2",
        "outputs": [
            {"context": {"lang": "en"}},  # missing output
        ],
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    with pytest.raises(ConfigError, match="must have 'output' field"):
        load_config(config_file)

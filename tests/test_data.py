import json
from pathlib import Path

import pytest

from kodudo.data.loader import load_data
from kodudo.errors import DataError


def test_load_data_plain_list(tmp_path: Path) -> None:
    """Test loading a plain JSON array."""
    data = [{"id": 1}, {"id": 2}]
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    loaded = load_data(data_file)
    assert len(loaded) == 2
    assert loaded.raw == tuple(data)
    assert not loaded.has_meta
    assert loaded.meta == {}


def test_load_data_aptoro(tmp_path: Path) -> None:
    """Test loading data in aptoro format (meta + data)."""
    data = {
        "meta": {"version": "1.0", "source": "test"},
        "data": [{"id": 1}, {"id": 2}],
    }
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    loaded = load_data(data_file)
    assert len(loaded) == 2
    assert loaded.has_meta
    assert loaded.meta == data["meta"]
    assert loaded.raw == tuple(data["data"])


def test_load_data_generic_wrapper(tmp_path: Path) -> None:
    """Test loading data wrapped in common keys like 'records' or 'items'."""
    data = {"records": [{"id": 1}]}
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    loaded = load_data(data_file)
    assert len(loaded) == 1
    assert not loaded.has_meta
    assert loaded.raw == tuple(data["records"])


def test_load_data_invalid_json(tmp_path: Path) -> None:
    """Test handling of invalid JSON syntax."""
    data_file = tmp_path / "data.json"
    data_file.write_text("{invalid", encoding="utf-8")

    with pytest.raises(DataError, match="Invalid JSON"):
        load_data(data_file)


def test_load_data_invalid_structure(tmp_path: Path) -> None:
    """Test JSON object without recognized data keys."""
    data = {"foo": "bar"}
    data_file = tmp_path / "data.json"
    with open(data_file, "w") as f:
        json.dump(data, f)

    with pytest.raises(DataError, match="Invalid JSON format"):
        load_data(data_file)


def test_load_data_file_not_found() -> None:
    """Test handling of non-existent file."""
    with pytest.raises(DataError, match="Data file not found"):
        load_data("non_existent.json")

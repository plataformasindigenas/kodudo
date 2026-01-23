import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from kodudo.__main__ import main
from kodudo.errors import KodudoError


@pytest.fixture
def mock_cook():
    with patch("kodudo.__main__.cook") as mock:
        yield mock


def test_cli_cook_single_file(mock_cook, tmp_path):
    """Test cooking a single file."""
    config = tmp_path / "config.yaml"
    config.touch()

    with patch.object(sys, "argv", ["kodudo", "cook", str(config)]):
        mock_cook.return_value = Path("output.html")
        exit_code = main()

    assert exit_code == 0
    mock_cook.assert_called_once_with(config)


def test_cli_cook_multiple_files(mock_cook, tmp_path):
    """Test cooking multiple files."""
    config1 = tmp_path / "config1.yaml"
    config2 = tmp_path / "config2.yaml"
    config1.touch()
    config2.touch()

    with patch.object(sys, "argv", ["kodudo", "cook", str(config1), str(config2)]):
        mock_cook.return_value = Path("output.html")
        exit_code = main()

    assert exit_code == 0
    assert mock_cook.call_count == 2
    mock_cook.assert_any_call(config1)
    mock_cook.assert_any_call(config2)


def test_cli_cook_missing_file(mock_cook, tmp_path):
    """Test behavior when a file is missing."""
    config1 = tmp_path / "existing.yaml"
    config1.touch()
    config2 = tmp_path / "missing.yaml"

    with patch.object(sys, "argv", ["kodudo", "cook", str(config1), str(config2)]):
        mock_cook.return_value = Path("output.html")
        exit_code = main()

    assert exit_code == 1
    # Should still process the existing file
    mock_cook.assert_called_once_with(config1)


def test_cli_cook_processing_error(mock_cook, tmp_path):
    """Test behavior when processing fails for one file."""
    config1 = tmp_path / "good.yaml"
    config2 = tmp_path / "bad.yaml"
    config3 = tmp_path / "good2.yaml"

    config1.touch()
    config2.touch()
    config3.touch()

    def side_effect(path):
        if path.name == "bad.yaml":
            raise KodudoError("Processing failed")
        return Path("output.html")

    mock_cook.side_effect = side_effect

    with patch.object(sys, "argv", ["kodudo", "cook", str(config1), str(config2), str(config3)]):
        exit_code = main()

    assert exit_code == 1
    assert mock_cook.call_count == 3

"""Data loader for kodudo.

Loads JSON files with aptoro metadata and provides access to both
raw dictionaries (for templates) and typed dataclasses (for programmatic use).
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodudo.errors import DataError


@dataclass(frozen=True)
class LoadedData:
    """Container for data loaded from aptoro JSON with metadata.

    Attributes:
        raw: List of record dictionaries (for template access)
        meta: Schema metadata dictionary
        has_meta: Whether the source had embedded metadata
    """

    raw: tuple[dict[str, Any], ...]
    meta: dict[str, Any]
    has_meta: bool

    def __len__(self) -> int:
        return len(self.raw)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.raw)


def load_data(path: str | Path) -> LoadedData:
    """Load JSON file, with or without aptoro metadata.

    Supports two formats:
    1. JSON with metadata: {"meta": {...}, "data": [...]}
    2. Plain JSON array: [...]

    Args:
        path: Path to JSON file

    Returns:
        LoadedData container with raw dicts and metadata

    Raises:
        DataError: If file cannot be read or has invalid format
    """
    path = Path(path)

    if not path.exists():
        raise DataError(f"Data file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        raise DataError(f"Invalid JSON in {path}: {e}") from e
    except OSError as e:
        raise DataError(f"Cannot read {path}: {e}") from e

    # Handle plain array format
    if isinstance(content, list):
        return LoadedData(
            raw=tuple(content),
            meta={},
            has_meta=False,
        )

    # Handle object format
    if not isinstance(content, dict):
        raise DataError("Invalid JSON format: expected object or array")

    # Check for aptoro metadata format
    if "meta" in content and "data" in content:
        meta = content["meta"]
        data = content["data"]

        if not isinstance(meta, dict):
            raise DataError("'meta' must be an object")

        if not isinstance(data, list):
            raise DataError("'data' must be an array")

        return LoadedData(
            raw=tuple(data),
            meta=meta,
            has_meta=True,
        )

    # Try common data keys
    for key in ("data", "records", "items", "results"):
        if key in content and isinstance(content[key], list):
            return LoadedData(
                raw=tuple(content[key]),
                meta={},
                has_meta=False,
            )

    raise DataError(
        "Invalid JSON format: expected array, or object with 'meta'/'data' keys, "
        "or object with 'data'/'records'/'items'/'results' key"
    )

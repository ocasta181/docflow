"""CLI output helpers."""

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import json
from pathlib import Path
from typing import Any


def add_json_argument(parser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )


def emit_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(_jsonable(payload), sort_keys=True))


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value

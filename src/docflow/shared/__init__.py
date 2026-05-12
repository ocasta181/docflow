"""Shared infrastructure for docflow domains."""

from .files import (
    PathValidationError,
    ensure_directory,
    ensure_file,
    ensure_output_not_inputs,
    find_files,
    has_extension,
    require_extension,
)
from .results import CommandResult
from .temp import atomic_output_path

__all__ = [
    "CommandResult",
    "PathValidationError",
    "atomic_output_path",
    "ensure_directory",
    "ensure_file",
    "ensure_output_not_inputs",
    "find_files",
    "has_extension",
    "require_extension",
]

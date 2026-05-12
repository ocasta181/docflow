"""Filesystem validation helpers."""

from collections.abc import Iterable
from pathlib import Path


class PathValidationError(ValueError):
    """Raised when a path fails a command precondition."""


def ensure_file(path: Path | str) -> Path:
    """Return a resolved file path or raise a validation error."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise PathValidationError(f"File not found: {resolved}")
    if not resolved.is_file():
        raise PathValidationError(f"Not a file: {resolved}")
    return resolved


def ensure_directory(path: Path | str) -> Path:
    """Return a resolved directory path or raise a validation error."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise PathValidationError(f"Directory not found: {resolved}")
    if not resolved.is_dir():
        raise PathValidationError(f"Not a directory: {resolved}")
    return resolved


def has_extension(path: Path | str, extensions: Iterable[str]) -> bool:
    """Return whether a path has one of the provided suffixes."""
    normalized = {_normalize_extension(extension) for extension in extensions}
    return Path(path).suffix.lower() in normalized


def require_extension(
    path: Path | str,
    extensions: Iterable[str],
    label: str,
) -> Path:
    """Return the path when its suffix matches, otherwise raise."""
    resolved = Path(path)
    if not has_extension(resolved, extensions):
        expected = ", ".join(sorted(_normalize_extension(ext) for ext in extensions))
        raise PathValidationError(f"{label} must have extension: {expected}")
    return resolved


def ensure_output_not_inputs(output_path: Path | str, input_paths: Iterable[Path | str]) -> Path:
    """Return output path unless it resolves to one of the input paths."""
    output = Path(output_path)
    output_resolved = output.expanduser().resolve()
    input_resolved = {Path(input_path).expanduser().resolve() for input_path in input_paths}
    if output_resolved in input_resolved:
        raise PathValidationError("Output path must be different from input paths")
    return output


def find_files(
    directory: Path | str,
    extensions: Iterable[str],
    recursive: bool = True,
) -> list[Path]:
    """Find files by extension under a directory."""
    root = ensure_directory(directory)
    normalized = {_normalize_extension(extension) for extension in extensions}
    pattern = "**/*" if recursive else "*"
    return sorted(
        path
        for path in root.glob(pattern)
        if path.is_file() and path.suffix.lower() in normalized
    )


def _normalize_extension(extension: str) -> str:
    return extension.lower() if extension.startswith(".") else f".{extension.lower()}"

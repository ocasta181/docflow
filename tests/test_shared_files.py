from pathlib import Path

import pytest

from docflow_cli.shared import (
    PathValidationError,
    ensure_directory,
    ensure_file,
    ensure_output_not_inputs,
    find_files,
    has_extension,
    require_extension,
)


def test_ensure_file_returns_resolved_file(tmp_path: Path) -> None:
    file_path = tmp_path / "input.pdf"
    file_path.write_text("content")

    assert ensure_file(file_path) == file_path.resolve()


def test_ensure_file_rejects_missing_path(tmp_path: Path) -> None:
    with pytest.raises(PathValidationError, match="File not found"):
        ensure_file(tmp_path / "missing.pdf")


def test_ensure_file_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(PathValidationError, match="Not a file"):
        ensure_file(tmp_path)


def test_ensure_directory_returns_resolved_directory(tmp_path: Path) -> None:
    directory = tmp_path / "docs"
    directory.mkdir()

    assert ensure_directory(directory) == directory.resolve()


def test_ensure_directory_rejects_file(tmp_path: Path) -> None:
    file_path = tmp_path / "input.pdf"
    file_path.write_text("content")

    with pytest.raises(PathValidationError, match="Not a directory"):
        ensure_directory(file_path)


def test_has_extension_is_case_insensitive(tmp_path: Path) -> None:
    assert has_extension(tmp_path / "SCAN.PDF", {"pdf"})
    assert has_extension(tmp_path / "scan.JPEG", {".jpg", ".jpeg"})
    assert not has_extension(tmp_path / "notes.txt", {".pdf"})


def test_require_extension_returns_path_when_suffix_matches(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.pdf"

    assert require_extension(file_path, {".pdf"}, "Input") == file_path


def test_require_extension_rejects_unexpected_suffix(tmp_path: Path) -> None:
    with pytest.raises(PathValidationError, match="Input must have extension"):
        require_extension(tmp_path / "scan.txt", {".pdf"}, "Input")


def test_find_files_returns_sorted_matching_files(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    first = tmp_path / "a.pdf"
    second = nested / "b.PDF"
    ignored = tmp_path / "notes.txt"
    first.write_text("a")
    second.write_text("b")
    ignored.write_text("c")

    assert find_files(tmp_path, {".pdf"}) == [first.resolve(), second.resolve()]


def test_find_files_can_skip_subdirectories(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    root_file = tmp_path / "root.pdf"
    nested_file = nested / "nested.pdf"
    root_file.write_text("root")
    nested_file.write_text("nested")

    assert find_files(tmp_path, {".pdf"}, recursive=False) == [root_file.resolve()]


def test_ensure_output_not_inputs_rejects_matching_path(tmp_path: Path) -> None:
    input_path = tmp_path / "input.pdf"
    input_path.write_text("content")

    with pytest.raises(PathValidationError, match="different from input"):
        ensure_output_not_inputs(input_path, [input_path])


def test_ensure_output_not_inputs_returns_output_path(tmp_path: Path) -> None:
    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "output.pdf"
    input_path.write_text("content")

    assert ensure_output_not_inputs(output_path, [input_path]) == output_path

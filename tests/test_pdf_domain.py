from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pliage.domains.pdf.service import join_pdfs, page_count, reverse_pdf, split_pdf
from pliage.shared import PathValidationError


def create_test_pdf(path: Path, widths: list[int]) -> Path:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=792)
    with path.open("wb") as file:
        writer.write(file)
    return path


def page_widths(path: Path) -> list[int]:
    reader = PdfReader(path)
    return [int(page.mediabox.width) for page in reader.pages]


def test_page_count_reads_pdf_page_total(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200, 300])

    assert page_count(input_pdf) == 3


def test_reverse_pdf_writes_reversed_sibling(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200, 300])

    result = reverse_pdf(input_pdf)

    assert result == tmp_path / "input_reversed.pdf"
    assert page_widths(result) == [300, 200, 100]
    assert page_widths(input_pdf) == [100, 200, 300]


def test_join_pdfs_preserves_input_order(tmp_path: Path) -> None:
    first = create_test_pdf(tmp_path / "first.pdf", [100, 200])
    second = create_test_pdf(tmp_path / "second.pdf", [300])
    output = tmp_path / "joined.pdf"

    result = join_pdfs(output, [first, second])

    assert result == output
    assert page_widths(output) == [100, 200, 300]


def test_join_pdfs_rejects_output_matching_input(tmp_path: Path) -> None:
    first = create_test_pdf(tmp_path / "first.pdf", [100])
    second = create_test_pdf(tmp_path / "second.pdf", [200])

    with pytest.raises(PathValidationError, match="different from input"):
        join_pdfs(first, [first, second])


def test_split_pdf_returns_part_page_ranges(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200, 300, 400, 500])

    parts = split_pdf(input_pdf, 2)

    assert [part.path.name for part in parts] == ["input_part1.pdf", "input_part2.pdf"]
    assert [(part.start_page, part.end_page) for part in parts] == [(1, 3), (4, 5)]
    assert [page_count(part.path) for part in parts] == [3, 2]


def test_split_pdf_distributes_remainder_to_earlier_parts(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", list(range(10)))

    parts = split_pdf(input_pdf, 3)

    assert [(part.start_page, part.end_page) for part in parts] == [(1, 4), (5, 7), (8, 10)]
    assert [page_count(part.path) for part in parts] == [4, 3, 3]


def test_split_pdf_rejects_more_parts_than_pages(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200])

    with pytest.raises(ValueError, match="cannot split into 3 parts"):
        split_pdf(input_pdf, 3)


def test_split_pdf_rejects_single_part(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200])

    with pytest.raises(ValueError, match="at least 2"):
        split_pdf(input_pdf, 1)


def test_join_pdfs_rejects_single_input(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100])

    with pytest.raises(ValueError, match="at least 2"):
        join_pdfs(tmp_path / "joined.pdf", [input_pdf])


def test_join_pdfs_rejects_missing_input(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100])

    with pytest.raises(PathValidationError, match="File not found"):
        join_pdfs(tmp_path / "joined.pdf", [input_pdf, tmp_path / "missing.pdf"])


def test_reverse_pdf_respects_explicit_output_path(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100, 200, 300])
    output_pdf = tmp_path / "custom.pdf"

    result = reverse_pdf(input_pdf, output_pdf)

    assert result == output_pdf
    assert page_widths(output_pdf) == [300, 200, 100]


def test_reverse_pdf_rejects_output_matching_input(tmp_path: Path) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", [100])

    with pytest.raises(PathValidationError, match="different from input"):
        reverse_pdf(input_pdf, input_pdf)

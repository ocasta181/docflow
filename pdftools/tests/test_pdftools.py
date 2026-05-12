"""Tests for pdftools split, join, and reverse functionality."""

import pytest
from pathlib import Path
from pypdf import PdfReader, PdfWriter

from pdftools import split_pdf, join_pdfs, reverse_pdf


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


def create_test_pdf(path: Path, num_pages: int) -> Path:
    """Create a test PDF with the specified number of pages."""
    writer = PdfWriter()
    for i in range(num_pages):
        # Create a blank page with some content
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)
    return path


def create_ordered_test_pdf(path: Path, widths: list[int]) -> Path:
    """Create a PDF whose page widths encode the original page order."""
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=792)
    with open(path, "wb") as f:
        writer.write(f)
    return path


class TestSplitPdf:
    """Tests for split_pdf function."""

    def test_split_into_two_equal_parts(self, temp_dir):
        """Split a 10-page PDF into 2 equal parts."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 10)

        result = split_pdf(input_pdf, num_parts=2)

        assert len(result) == 2
        assert result[0].name == "test_part1.pdf"
        assert result[1].name == "test_part2.pdf"

        reader1 = PdfReader(result[0])
        reader2 = PdfReader(result[1])
        assert len(reader1.pages) == 5
        assert len(reader2.pages) == 5

    def test_split_into_three_parts_uneven(self, temp_dir):
        """Split a 10-page PDF into 3 parts (4, 3, 3)."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 10)

        result = split_pdf(input_pdf, num_parts=3)

        assert len(result) == 3
        reader1 = PdfReader(result[0])
        reader2 = PdfReader(result[1])
        reader3 = PdfReader(result[2])
        # Remainder distributed to first parts
        assert len(reader1.pages) == 4
        assert len(reader2.pages) == 3
        assert len(reader3.pages) == 3

    def test_split_into_four_parts(self, temp_dir):
        """Split a 12-page PDF into 4 equal parts."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 12)

        result = split_pdf(input_pdf, num_parts=4)

        assert len(result) == 4
        for part in result:
            reader = PdfReader(part)
            assert len(reader.pages) == 3

    def test_split_preserves_original(self, temp_dir):
        """Verify original file is not modified."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 6)
        original_size = input_pdf.stat().st_size

        split_pdf(input_pdf, num_parts=2)

        assert input_pdf.exists()
        assert input_pdf.stat().st_size == original_size

    def test_split_too_few_pages_raises(self, temp_dir):
        """Splitting into more parts than pages should raise."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 2)

        with pytest.raises(ValueError, match="cannot split into 3 parts"):
            split_pdf(input_pdf, num_parts=3)

    def test_split_one_part_raises(self, temp_dir):
        """Splitting into 1 part should raise."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 4)

        with pytest.raises(ValueError, match="at least 2"):
            split_pdf(input_pdf, num_parts=1)

    def test_split_default_is_two_parts(self, temp_dir):
        """Default split should be into 2 parts."""
        input_pdf = create_test_pdf(temp_dir / "test.pdf", 4)

        result = split_pdf(input_pdf)

        assert len(result) == 2


class TestJoinPdfs:
    """Tests for join_pdfs function."""

    def test_join_two_pdfs(self, temp_dir):
        """Join two PDFs into one."""
        pdf1 = create_test_pdf(temp_dir / "part1.pdf", 3)
        pdf2 = create_test_pdf(temp_dir / "part2.pdf", 5)
        output = temp_dir / "joined.pdf"

        result = join_pdfs(output, [pdf1, pdf2])

        assert result == output
        assert output.exists()
        reader = PdfReader(output)
        assert len(reader.pages) == 8

    def test_join_multiple_pdfs(self, temp_dir):
        """Join multiple PDFs into one."""
        pdfs = [
            create_test_pdf(temp_dir / f"part{i}.pdf", i + 1)
            for i in range(4)
        ]
        output = temp_dir / "joined.pdf"

        result = join_pdfs(output, pdfs)

        reader = PdfReader(result)
        # 1 + 2 + 3 + 4 = 10 pages
        assert len(reader.pages) == 10

    def test_join_preserves_originals(self, temp_dir):
        """Verify original files are not modified."""
        pdf1 = create_test_pdf(temp_dir / "part1.pdf", 3)
        pdf2 = create_test_pdf(temp_dir / "part2.pdf", 5)
        size1 = pdf1.stat().st_size
        size2 = pdf2.stat().st_size
        output = temp_dir / "joined.pdf"

        join_pdfs(output, [pdf1, pdf2])

        assert pdf1.exists()
        assert pdf2.exists()
        assert pdf1.stat().st_size == size1
        assert pdf2.stat().st_size == size2

    def test_join_single_pdf_raises(self, temp_dir):
        """Joining a single PDF should raise."""
        pdf1 = create_test_pdf(temp_dir / "single.pdf", 3)
        output = temp_dir / "joined.pdf"

        with pytest.raises(ValueError, match="at least 2"):
            join_pdfs(output, [pdf1])

    def test_join_missing_file_raises(self, temp_dir):
        """Joining with a missing file should raise."""
        pdf1 = create_test_pdf(temp_dir / "exists.pdf", 3)
        missing = temp_dir / "missing.pdf"
        output = temp_dir / "joined.pdf"

        with pytest.raises(FileNotFoundError):
            join_pdfs(output, [pdf1, missing])

    def test_join_output_matching_input_raises(self, temp_dir):
        """Joining should not overwrite one of its source PDFs."""
        pdf1 = create_test_pdf(temp_dir / "part1.pdf", 3)
        pdf2 = create_test_pdf(temp_dir / "part2.pdf", 5)

        with pytest.raises(ValueError, match="different from input"):
            join_pdfs(pdf1, [pdf1, pdf2])


class TestReversePdf:
    """Tests for reverse_pdf function."""

    def test_reverse_pdf_default_output_name(self, temp_dir):
        """Reverse a PDF and write to the default sibling output."""
        input_pdf = create_ordered_test_pdf(temp_dir / "ordered.pdf", [100, 200, 300])

        result = reverse_pdf(input_pdf)

        assert result == temp_dir / "ordered_reversed.pdf"
        assert result.exists()

    def test_reverse_pdf_reverses_page_order(self, temp_dir):
        """Reverse should invert the page order."""
        input_pdf = create_ordered_test_pdf(temp_dir / "ordered.pdf", [100, 200, 300, 400])

        result = reverse_pdf(input_pdf)
        reader = PdfReader(result)

        assert [int(page.mediabox.width) for page in reader.pages] == [400, 300, 200, 100]

    def test_reverse_pdf_preserves_original(self, temp_dir):
        """Reverse should not modify the input file."""
        input_pdf = create_ordered_test_pdf(temp_dir / "ordered.pdf", [100, 200, 300])
        original_reader = PdfReader(input_pdf)
        original_order = [int(page.mediabox.width) for page in original_reader.pages]
        original_size = input_pdf.stat().st_size

        reverse_pdf(input_pdf)

        reread_original = PdfReader(input_pdf)
        assert [int(page.mediabox.width) for page in reread_original.pages] == original_order
        assert input_pdf.stat().st_size == original_size

    def test_reverse_pdf_with_explicit_output(self, temp_dir):
        """Reverse should respect an explicit output path."""
        input_pdf = create_ordered_test_pdf(temp_dir / "ordered.pdf", [100, 200, 300])
        output = temp_dir / "custom-output.pdf"

        result = reverse_pdf(input_pdf, output)

        assert result == output
        assert output.exists()

    def test_reverse_pdf_same_input_and_output_raises(self, temp_dir):
        """Reverse should reject overwriting the source file."""
        input_pdf = create_ordered_test_pdf(temp_dir / "ordered.pdf", [100, 200, 300])

        with pytest.raises(ValueError, match="different from input"):
            reverse_pdf(input_pdf, input_pdf)


class TestRoundTrip:
    """Test split and join together."""

    def test_split_then_join_preserves_page_count(self, temp_dir):
        """Splitting and joining should preserve total page count."""
        original = create_test_pdf(temp_dir / "original.pdf", 10)

        parts = split_pdf(original, num_parts=3)
        rejoined = temp_dir / "rejoined.pdf"
        join_pdfs(rejoined, parts)

        original_reader = PdfReader(original)
        rejoined_reader = PdfReader(rejoined)
        assert len(rejoined_reader.pages) == len(original_reader.pages)

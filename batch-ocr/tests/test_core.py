"""Tests for batch_ocr.core module."""

import pytest
from pathlib import Path

from batch_ocr.core import find_pdfs, has_text, ocr_pdf, ocr_directory, extract_text, OcrResult, ExtractResult


class TestFindPdfs:
    """Tests for find_pdfs function."""

    def test_finds_pdfs_in_directory(self, temp_dir, pdf_with_text):
        """Should find PDF files in a directory."""
        pdfs = find_pdfs(temp_dir, recursive=False)
        assert len(pdfs) == 1
        assert pdfs[0].name == "with_text.pdf"

    def test_finds_pdfs_recursively(self, nested_pdf_dir):
        """Should find PDFs in subdirectories when recursive=True."""
        pdfs = find_pdfs(nested_pdf_dir, recursive=True)
        assert len(pdfs) == 4  # root.pdf, file1.pdf, file2.pdf, with_text.pdf

    def test_non_recursive_ignores_subdirs(self, nested_pdf_dir):
        """Should not find PDFs in subdirectories when recursive=False."""
        pdfs = find_pdfs(nested_pdf_dir, recursive=False)
        assert len(pdfs) == 1
        assert pdfs[0].name == "root.pdf"

    def test_empty_directory(self, temp_dir):
        """Should return empty list for directory with no PDFs."""
        pdfs = find_pdfs(temp_dir, recursive=True)
        assert pdfs == []

    def test_returns_sorted_paths(self, nested_pdf_dir):
        """Should return paths in sorted order."""
        pdfs = find_pdfs(nested_pdf_dir, recursive=True)
        # Paths should be sorted, not just names
        assert pdfs == sorted(pdfs)


class TestHasText:
    """Tests for has_text function."""

    def test_pdf_with_text_returns_true(self, pdf_with_text):
        """Should return True for PDF with extractable text."""
        assert has_text(pdf_with_text) is True

    def test_pdf_without_text_returns_false(self, pdf_without_text):
        """Should return False for PDF without extractable text."""
        assert has_text(pdf_without_text) is False

    def test_respects_min_chars_threshold(self, pdf_with_text):
        """Should respect the min_chars threshold."""
        # With very high threshold, should return False
        assert has_text(pdf_with_text, min_chars=10000) is False

    def test_nonexistent_file_returns_false(self, temp_dir):
        """Should return False for nonexistent file."""
        assert has_text(temp_dir / "nonexistent.pdf") is False


class TestOcrPdf:
    """Tests for ocr_pdf function."""

    def test_skips_pdf_with_text(self, pdf_with_text):
        """Should skip OCR for PDF that already has text."""
        result = ocr_pdf(pdf_with_text, skip_if_text=True)
        assert result.success is True
        assert result.skipped is True
        assert "Already has text" in result.message

    def test_processes_pdf_without_text(self, pdf_with_image):
        """Should run OCR on PDF without text."""
        result = ocr_pdf(pdf_with_image, skip_if_text=True)
        assert result.success is True
        assert result.skipped is False
        assert "OCR completed" in result.message

    def test_force_ocr_on_text_pdf(self, pdf_with_text):
        """Should run OCR even on PDF with text when skip_if_text=False."""
        result = ocr_pdf(pdf_with_text, skip_if_text=False)
        assert result.success is True
        assert result.skipped is False

    def test_nonexistent_file_returns_error(self, temp_dir):
        """Should return error for nonexistent file."""
        result = ocr_pdf(temp_dir / "nonexistent.pdf")
        assert result.success is False
        assert result.skipped is False
        assert "not found" in result.message.lower()

    def test_saves_to_custom_output_path(self, pdf_with_image, temp_dir):
        """Should save to custom output path when specified."""
        output_path = temp_dir / "output.pdf"
        result = ocr_pdf(pdf_with_image, output_path=output_path, skip_if_text=True)

        assert result.success is True
        assert result.skipped is False
        assert output_path.exists()
        # Original should be unchanged
        assert pdf_with_image.exists()


class TestOcrDirectory:
    """Tests for ocr_directory function."""

    def test_processes_all_pdfs(self, nested_pdf_dir):
        """Should process all PDFs in directory."""
        results = ocr_directory(nested_pdf_dir, recursive=True)
        assert len(results) == 4

    def test_non_recursive_only_processes_root(self, nested_pdf_dir):
        """Should only process root PDFs when recursive=False."""
        results = ocr_directory(nested_pdf_dir, recursive=False)
        assert len(results) == 1

    def test_callback_is_called(self, nested_pdf_dir):
        """Should call callback for each file."""
        called = []

        def callback(path, index, total):
            called.append((path.name, index, total))

        ocr_directory(nested_pdf_dir, recursive=True, callback=callback)
        assert len(called) == 4
        # Check indices are correct
        indices = [c[1] for c in called]
        assert indices == [0, 1, 2, 3]

    def test_invalid_directory_raises_error(self, temp_dir):
        """Should raise ValueError for non-directory path."""
        fake_dir = temp_dir / "not_a_dir"
        with pytest.raises(ValueError, match="Not a directory"):
            ocr_directory(fake_dir)

    def test_returns_ocr_results(self, nested_pdf_dir):
        """Should return list of OcrResult objects."""
        results = ocr_directory(nested_pdf_dir, recursive=True)
        assert all(isinstance(r, OcrResult) for r in results)


class TestExtractText:
    """Tests for extract_text function."""

    def test_extracts_existing_text(self, pdf_with_text):
        """Should extract text from PDF that already has text."""
        result = extract_text(pdf_with_text)
        assert result.success is True
        assert result.ocr_performed is False
        assert result.output_path.exists()
        assert result.output_path.suffix == ".txt"
        # Check the text was actually extracted
        text = result.output_path.read_text()
        assert len(text) > 0
        assert "test PDF" in text.lower() or "extractable text" in text.lower()

    def test_runs_ocr_when_no_text(self, pdf_with_image):
        """Should run OCR first when PDF has no text."""
        result = extract_text(pdf_with_image, ocr_if_needed=True)
        assert result.success is True
        assert result.ocr_performed is True
        assert result.output_path.exists()
        assert "OCR'd and extracted" in result.message

    def test_custom_output_path(self, pdf_with_text, temp_dir):
        """Should save to custom output path when specified."""
        output_path = temp_dir / "custom_output.txt"
        result = extract_text(pdf_with_text, output_path=output_path)
        assert result.success is True
        assert result.output_path == output_path
        assert output_path.exists()

    def test_default_output_path_same_directory(self, pdf_with_text):
        """Should create .txt file in same directory as PDF by default."""
        result = extract_text(pdf_with_text)
        assert result.success is True
        assert result.output_path.parent == pdf_with_text.parent
        assert result.output_path.stem == pdf_with_text.stem
        assert result.output_path.suffix == ".txt"

    def test_nonexistent_file_returns_error(self, temp_dir):
        """Should return error for nonexistent file."""
        result = extract_text(temp_dir / "nonexistent.pdf")
        assert result.success is False
        assert result.ocr_performed is False
        assert "not found" in result.message.lower()

    def test_returns_extract_result(self, pdf_with_text):
        """Should return ExtractResult object."""
        result = extract_text(pdf_with_text)
        assert isinstance(result, ExtractResult)

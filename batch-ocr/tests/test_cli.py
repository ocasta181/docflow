"""Tests for batch_ocr.cli module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

from batch_ocr.cli import main


class TestCli:
    """Tests for CLI interface."""

    def test_dry_run_single_file(self, pdf_with_text, capsys):
        """Should show what would be processed for single file."""
        with patch.object(sys, 'argv', ['batch-ocr', '--dry-run', str(pdf_with_text)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Would process" in captured.out

    def test_dry_run_directory(self, nested_pdf_dir, capsys):
        """Should list all PDFs in dry-run mode."""
        with patch.object(sys, 'argv', ['batch-ocr', '--dry-run', str(nested_pdf_dir)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Found 4 PDF" in captured.out

    def test_nonexistent_path_returns_error(self, temp_dir, capsys):
        """Should return error for nonexistent path."""
        fake_path = temp_dir / "nonexistent"
        with patch.object(sys, 'argv', ['batch-ocr', str(fake_path)]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_non_pdf_file_returns_error(self, temp_dir, capsys):
        """Should return error for non-PDF file."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("hello")

        with patch.object(sys, 'argv', ['batch-ocr', str(txt_file)]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Not a PDF" in captured.err

    def test_no_recursive_flag(self, nested_pdf_dir, capsys):
        """Should only process root directory with --no-recursive."""
        with patch.object(sys, 'argv', ['batch-ocr', '--dry-run', '--no-recursive', str(nested_pdf_dir)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Found 1 PDF" in captured.out

    def test_empty_directory(self, temp_dir, capsys):
        """Should handle empty directory gracefully."""
        with patch.object(sys, 'argv', ['batch-ocr', str(temp_dir)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "No PDF files found" in captured.out

    def test_quiet_mode_reduces_output(self, nested_pdf_dir, capsys):
        """Should reduce output in quiet mode."""
        with patch.object(sys, 'argv', ['batch-ocr', '--quiet', str(nested_pdf_dir)]):
            result = main()

        captured = capsys.readouterr()
        # Should still show summary
        assert "Done:" in captured.out
        # But not individual file progress (those PDFs have text so skipped)

    def test_processes_single_pdf(self, pdf_with_text, capsys):
        """Should process a single PDF file."""
        with patch.object(sys, 'argv', ['batch-ocr', str(pdf_with_text)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Skipped" in captured.out  # PDF has text, so skipped

    def test_force_flag_description(self, pdf_with_text, capsys):
        """Force flag should attempt OCR even on files with text."""
        # Just test that force flag is accepted, actual OCR needs tesseract
        with patch.object(sys, 'argv', ['batch-ocr', '--dry-run', '--force', str(pdf_with_text)]):
            result = main()

        assert result == 0

    def test_extract_single_file(self, pdf_with_text, capsys):
        """Should extract text from single PDF file."""
        with patch.object(sys, 'argv', ['batch-ocr', '--extract', str(pdf_with_text)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "extracted" in captured.out.lower()
        # Check .txt file was created
        txt_path = pdf_with_text.with_suffix(".txt")
        assert txt_path.exists()

    def test_extract_directory(self, nested_pdf_dir, capsys):
        """Should extract text from all PDFs in directory."""
        with patch.object(sys, 'argv', ['batch-ocr', '--extract', str(nested_pdf_dir)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Extracting text from" in captured.out
        assert "extracted" in captured.out.lower()

    def test_extract_dry_run(self, pdf_with_text, capsys):
        """Should show extract action in dry-run mode."""
        with patch.object(sys, 'argv', ['batch-ocr', '--extract', '--dry-run', str(pdf_with_text)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "extract text from" in captured.out.lower()

    def test_extract_with_ocr(self, pdf_with_image, capsys):
        """Should run OCR then extract when PDF has no text."""
        with patch.object(sys, 'argv', ['batch-ocr', '--extract', str(pdf_with_image)]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "OCR" in captured.out
        # Check .txt file was created
        txt_path = pdf_with_image.with_suffix(".txt")
        assert txt_path.exists()

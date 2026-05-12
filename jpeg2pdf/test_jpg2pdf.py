#!/usr/bin/env python3
"""
End-to-end tests for jpg2pdf.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


def create_test_jpeg(path: Path, width: int = 200, height: int = 300, color: tuple = (255, 0, 0)):
    """Create a test JPEG image."""
    img = Image.new('RGB', (width, height), color)
    img.save(path, 'JPEG')


def run_jpg2pdf(*args, cwd: Path) -> subprocess.CompletedProcess:
    """Run the jpg2pdf script."""
    script = Path(__file__).parent / 'jpg2pdf.py'
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        capture_output=True,
        text=True
    )


def test_basic_grouping():
    """Test that files are grouped by prefix and combined into PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test images for two groups
        create_test_jpeg(tmpdir / 'invoice_1.jpg', color=(255, 0, 0))
        create_test_jpeg(tmpdir / 'invoice_2.jpg', color=(0, 255, 0))
        create_test_jpeg(tmpdir / 'receipt_1.jpg', color=(0, 0, 255))

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert (tmpdir / 'pdfs' / 'invoice.pdf').exists(), "invoice.pdf not created"
        assert (tmpdir / 'pdfs' / 'receipt.pdf').exists(), "receipt.pdf not created"

        # Verify page counts
        invoice_pdf = PdfReader(tmpdir / 'pdfs' / 'invoice.pdf')
        receipt_pdf = PdfReader(tmpdir / 'pdfs' / 'receipt.pdf')
        assert len(invoice_pdf.pages) == 2, f"Expected 2 pages in invoice.pdf, got {len(invoice_pdf.pages)}"
        assert len(receipt_pdf.pages) == 1, f"Expected 1 page in receipt.pdf, got {len(receipt_pdf.pages)}"

        print("✓ test_basic_grouping passed")


def test_case_insensitive_grouping():
    """Test that grouping is case-insensitive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Mixed case should group together
        create_test_jpeg(tmpdir / 'Tax_1.jpg')
        create_test_jpeg(tmpdir / 'tax_2.jpg')
        create_test_jpeg(tmpdir / 'TAX_3.jpg')

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"

        # Should create exactly one PDF
        pdfs = list((tmpdir / 'pdfs').glob('*.pdf'))
        assert len(pdfs) == 1, f"Expected 1 PDF, got {len(pdfs)}: {pdfs}"

        # Should have 3 pages
        pdf = PdfReader(pdfs[0])
        assert len(pdf.pages) == 3, f"Expected 3 pages, got {len(pdf.pages)}"

        print("✓ test_case_insensitive_grouping passed")


def test_numeric_sorting():
    """Test that sequence numbers are sorted numerically, not lexicographically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create files that would sort wrong lexicographically
        for i in [1, 2, 10, 11, 20, 3]:
            create_test_jpeg(tmpdir / f'doc_{i}.jpg', color=(i * 10, i * 10, i * 10))

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"

        pdf = PdfReader(tmpdir / 'pdfs' / 'doc.pdf')
        assert len(pdf.pages) == 6, f"Expected 6 pages, got {len(pdf.pages)}"

        print("✓ test_numeric_sorting passed")


def test_sequence_gap_warning():
    """Test that gaps in sequence numbers produce warnings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create files with gaps (missing 2 and 4)
        create_test_jpeg(tmpdir / 'doc_1.jpg')
        create_test_jpeg(tmpdir / 'doc_3.jpg')
        create_test_jpeg(tmpdir / 'doc_5.jpg')

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert 'missing sequence number' in result.stderr.lower(), f"Expected gap warning, got: {result.stderr}"
        assert '2' in result.stderr and '4' in result.stderr, f"Expected [2, 4] in warning: {result.stderr}"

        # Should still create PDF with available files
        pdf = PdfReader(tmpdir / 'pdfs' / 'doc.pdf')
        assert len(pdf.pages) == 3

        print("✓ test_sequence_gap_warning passed")


def test_prefix_filter():
    """Test --prefix flag filters to specific group."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        create_test_jpeg(tmpdir / 'invoice_1.jpg')
        create_test_jpeg(tmpdir / 'invoice_2.jpg')
        create_test_jpeg(tmpdir / 'receipt_1.jpg')

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), '--prefix', 'invoice', cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert (tmpdir / 'pdfs' / 'invoice.pdf').exists()
        assert not (tmpdir / 'pdfs' / 'receipt.pdf').exists(), "receipt.pdf should not be created"

        print("✓ test_prefix_filter passed")


def test_skip_non_matching_files():
    """Test that files not matching the pattern are skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        create_test_jpeg(tmpdir / 'doc_1.jpg')  # Valid
        create_test_jpeg(tmpdir / 'random.jpg')  # No sequence number
        create_test_jpeg(tmpdir / 'doc.jpg')     # No underscore + number
        (tmpdir / 'notes.txt').write_text('hello')  # Not a JPEG

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0
        assert 'Skipping' in result.stderr, "Should log skipped files"

        pdfs = list((tmpdir / 'pdfs').glob('*.pdf'))
        assert len(pdfs) == 1
        assert pdfs[0].name == 'doc.pdf'

        print("✓ test_skip_non_matching_files passed")


def test_no_valid_files_error():
    """Test that error is returned when no valid files found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create only non-matching files
        create_test_jpeg(tmpdir / 'random.jpg')

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode != 0, "Should fail with no valid files"
        assert 'no valid files' in result.stderr.lower()

        print("✓ test_no_valid_files_error passed")


def test_jpeg_extension_variants():
    """Test that both .jpg and .jpeg extensions work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        create_test_jpeg(tmpdir / 'doc_1.jpg')
        create_test_jpeg(tmpdir / 'doc_2.jpeg')
        create_test_jpeg(tmpdir / 'doc_3.JPG')   # Uppercase
        create_test_jpeg(tmpdir / 'doc_4.JPEG')  # Uppercase

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"

        pdf = PdfReader(tmpdir / 'pdfs' / 'doc.pdf')
        assert len(pdf.pages) == 4, f"Expected 4 pages, got {len(pdf.pages)}"

        print("✓ test_jpeg_extension_variants passed")


def test_default_output_directory():
    """Test that default output is ./pdfs/"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        create_test_jpeg(tmpdir / 'doc_1.jpg')

        result = run_jpg2pdf(str(tmpdir), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert (tmpdir / 'pdfs' / 'doc.pdf').exists()

        print("✓ test_default_output_directory passed")


def test_numbers_in_prefix():
    """Test that prefixes containing numbers are handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Prefix contains numbers - only final _N should be sequence
        create_test_jpeg(tmpdir / 'Bank_statement_july_2023_1.jpg')
        create_test_jpeg(tmpdir / 'Bank_statement_july_2023_2.jpg')
        create_test_jpeg(tmpdir / 'Bank_statement_july_2023_3.jpg')

        result = run_jpg2pdf(str(tmpdir), '-o', str(tmpdir / 'pdfs'), cwd=tmpdir)

        assert result.returncode == 0, f"Failed: {result.stderr}"

        # Should create one PDF with the full prefix
        expected_pdf = tmpdir / 'pdfs' / 'Bank_statement_july_2023.pdf'
        assert expected_pdf.exists(), f"Expected {expected_pdf.name}, got: {list((tmpdir / 'pdfs').glob('*.pdf'))}"

        pdf = PdfReader(expected_pdf)
        assert len(pdf.pages) == 3, f"Expected 3 pages, got {len(pdf.pages)}"

        print("✓ test_numbers_in_prefix passed")


def main():
    """Run all tests."""
    print("Running jpg2pdf end-to-end tests...\n")

    tests = [
        test_basic_grouping,
        test_case_insensitive_grouping,
        test_numeric_sorting,
        test_sequence_gap_warning,
        test_prefix_filter,
        test_skip_non_matching_files,
        test_no_valid_files_error,
        test_jpeg_extension_variants,
        test_default_output_directory,
        test_numbers_in_prefix,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

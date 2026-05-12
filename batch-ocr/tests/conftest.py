"""Test fixtures for batch-ocr."""

import pytest
from pathlib import Path
import tempfile
import shutil

import fitz  # PyMuPDF


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)


@pytest.fixture
def pdf_with_text(temp_dir):
    """Create a PDF that has extractable text."""
    pdf_path = temp_dir / "with_text.pdf"
    doc = fitz.open()
    page = doc.new_page()

    # Insert enough text to pass the threshold
    text = "This is a test PDF with extractable text content. " * 10
    page.insert_text((50, 50), text, fontsize=12)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def pdf_without_text(temp_dir):
    """Create a PDF that has no extractable text (image-only)."""
    pdf_path = temp_dir / "without_text.pdf"
    doc = fitz.open()
    page = doc.new_page()

    # Create a simple image with text drawn as graphics (not extractable)
    # Draw a rectangle as placeholder for "scanned" content
    rect = fitz.Rect(50, 50, 500, 100)
    page.draw_rect(rect, color=(0, 0, 0), width=1)

    # Note: This creates a PDF with graphics but no text layer
    # For a true "scanned" PDF test, we'd need an actual image

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def pdf_with_image(temp_dir):
    """Create a PDF with an embedded image containing text (for OCR testing)."""
    pdf_path = temp_dir / "image_pdf.pdf"
    doc = fitz.open()
    page = doc.new_page()

    # Create a pixmap with text rendered as an image
    text_doc = fitz.open()
    text_page = text_doc.new_page(width=400, height=100)
    text_page.insert_text((10, 50), "Sample OCR Test Text", fontsize=24)
    pix = text_page.get_pixmap(dpi=150)
    text_doc.close()

    # Insert the image into our PDF
    page.insert_image(fitz.Rect(50, 50, 450, 150), pixmap=pix)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def nested_pdf_dir():
    """Create a directory structure with PDFs in subdirectories."""
    path = Path(tempfile.mkdtemp())

    # Create subdirectories
    sub1 = path / "subdir1"
    sub2 = path / "subdir2"
    sub1.mkdir()
    sub2.mkdir()

    # Create PDFs in various locations
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test content " * 20, fontsize=12)

    doc.save(str(path / "root.pdf"))
    doc.save(str(sub1 / "file1.pdf"))
    doc.save(str(sub1 / "file2.pdf"))
    doc.save(str(sub2 / "file3.pdf"))
    doc.close()

    yield path
    shutil.rmtree(path)

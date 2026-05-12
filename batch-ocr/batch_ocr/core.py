"""Core OCR functions for batch processing PDFs."""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
import subprocess
import tempfile
import shutil

import fitz  # PyMuPDF


def _get_bundle_dir() -> Path | None:
    """Get the PyInstaller bundle directory, or None if not frozen."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return None


def _get_tesseract_cmd() -> str:
    """Get the path to the tesseract executable."""
    bundle_dir = _get_bundle_dir()
    if bundle_dir:
        return str(bundle_dir / "tesseract")
    return "tesseract"


def _get_tesseract_env() -> dict:
    """Get environment variables for tesseract subprocess."""
    env = os.environ.copy()
    bundle_dir = _get_bundle_dir()
    if bundle_dir:
        env["TESSDATA_PREFIX"] = str(bundle_dir / "tessdata")
    return env


@dataclass
class OcrResult:
    """Result of OCR processing for a single file."""
    path: Path
    success: bool
    skipped: bool
    message: str


def has_text(pdf_path: Path, min_chars: int = 100) -> bool:
    """
    Check if a PDF has extractable text content.

    Args:
        pdf_path: Path to the PDF file
        min_chars: Minimum characters to consider the PDF as having text

    Returns:
        True if the PDF has extractable text, False otherwise.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
            if len(text) >= min_chars:
                doc.close()
                return True
        doc.close()
        return len(text.strip()) >= min_chars
    except Exception:
        return False


def ocr_pdf(pdf_path: Path, output_path: Path | None = None, skip_if_text: bool = True) -> OcrResult:
    """
    Run OCR on a single PDF file.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path for output file. If None, overwrites the input file.
        skip_if_text: Skip OCR if the PDF already has text

    Returns:
        OcrResult with status information.
    """
    if not pdf_path.exists():
        return OcrResult(pdf_path, success=False, skipped=False, message="File not found")

    if skip_if_text and has_text(pdf_path):
        return OcrResult(pdf_path, success=True, skipped=True, message="Already has text")

    # If no output path, use a temp file then replace original
    in_place = output_path is None
    if in_place:
        output_path = Path(tempfile.mktemp(suffix=".pdf"))

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Check if page already has text
            if skip_if_text and len(page.get_text().strip()) > 50:
                continue

            # Render page to image
            pix = page.get_pixmap(dpi=300)
            img_path = Path(tempfile.mktemp(suffix=".png"))
            pix.save(str(img_path))

            # Run tesseract to get PDF with text layer
            pdf_path_out = Path(tempfile.mktemp(suffix=""))
            result = subprocess.run(
                [
                    _get_tesseract_cmd(),
                    str(img_path),
                    str(pdf_path_out),
                    "-l", "eng",
                    "pdf",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env=_get_tesseract_env(),
            )

            img_path.unlink()

            if result.returncode != 0:
                error = result.stderr.strip() or "Tesseract failed"
                return OcrResult(pdf_path, success=False, skipped=False, message=error)

            # Extract text from tesseract PDF and insert into original
            ocr_pdf_path = Path(str(pdf_path_out) + ".pdf")
            if ocr_pdf_path.exists():
                ocr_doc = fitz.open(ocr_pdf_path)
                ocr_page = ocr_doc[0]

                # Get text dict from OCR'd page and insert into original
                text_page = ocr_page.get_textpage()
                blocks = ocr_page.get_text("dict", textpage=text_page)["blocks"]

                for block in blocks:
                    if block["type"] == 0:  # text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                # Insert invisible text at the correct position
                                rect = fitz.Rect(span["bbox"])
                                # Scale rect from 300 DPI image coords to page coords
                                scale = page.rect.width / pix.width
                                scaled_rect = rect * scale

                                page.insert_textbox(
                                    scaled_rect,
                                    span["text"],
                                    fontsize=span["size"] * scale,
                                    render_mode=3,  # invisible
                                )

                ocr_doc.close()
                ocr_pdf_path.unlink()

        doc.save(str(output_path))
        doc.close()

        if in_place:
            shutil.move(str(output_path), str(pdf_path))

        return OcrResult(pdf_path, success=True, skipped=False, message="OCR completed")

    except subprocess.TimeoutExpired:
        if in_place and output_path.exists():
            output_path.unlink()
        return OcrResult(pdf_path, success=False, skipped=False, message="Timeout")
    except Exception as e:
        if in_place and output_path.exists():
            output_path.unlink()
        return OcrResult(pdf_path, success=False, skipped=False, message=str(e))


@dataclass
class ExtractResult:
    """Result of text extraction for a single file."""
    path: Path
    output_path: Path | None
    success: bool
    ocr_performed: bool
    message: str


def extract_text(pdf_path: Path, output_path: Path | None = None, ocr_if_needed: bool = True) -> ExtractResult:
    """
    Extract text from a PDF, running OCR first if needed.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path for output .txt file. If None, uses same name as PDF with .txt extension.
        ocr_if_needed: Run OCR if no text is found

    Returns:
        ExtractResult with status information.
    """
    if not pdf_path.exists():
        return ExtractResult(pdf_path, None, success=False, ocr_performed=False, message="File not found")

    if output_path is None:
        output_path = pdf_path.with_suffix(".txt")

    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

        # If no text found and OCR is enabled, run OCR first
        ocr_performed = False
        if len(text.strip()) < 100 and ocr_if_needed:
            ocr_result = ocr_pdf(pdf_path, skip_if_text=False)
            if not ocr_result.success:
                return ExtractResult(pdf_path, None, success=False, ocr_performed=False, message=f"OCR failed: {ocr_result.message}")

            ocr_performed = True

            # Re-extract text after OCR
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()

        # Write text to file
        output_path.write_text(text.strip())

        if ocr_performed:
            return ExtractResult(pdf_path, output_path, success=True, ocr_performed=True, message="OCR'd and extracted")
        else:
            return ExtractResult(pdf_path, output_path, success=True, ocr_performed=False, message="Extracted existing text")

    except Exception as e:
        return ExtractResult(pdf_path, None, success=False, ocr_performed=False, message=str(e))


def find_pdfs(directory: Path, recursive: bool = True) -> list[Path]:
    """
    Find all PDF files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories

    Returns:
        List of paths to PDF files.
    """
    pattern = "**/*.pdf" if recursive else "*.pdf"
    return sorted(directory.glob(pattern))


def ocr_directory(
    directory: Path,
    recursive: bool = True,
    skip_if_text: bool = True,
    callback: callable = None,
) -> list[OcrResult]:
    """
    Run OCR on all PDFs in a directory.

    Args:
        directory: Directory to process
        recursive: Whether to process subdirectories
        skip_if_text: Skip PDFs that already have extractable text
        callback: Optional callback(pdf_path, index, total) called before processing each file

    Returns:
        List of OcrResult for each processed file.
    """
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    pdfs = find_pdfs(directory, recursive)
    results = []

    for i, pdf_path in enumerate(pdfs):
        if callback:
            callback(pdf_path, i, len(pdfs))

        result = ocr_pdf(pdf_path, skip_if_text=skip_if_text)
        results.append(result)

    return results

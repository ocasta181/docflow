"""OCR and text extraction service."""

from collections.abc import Callable
from pathlib import Path
import shutil
import subprocess
import tempfile

import fitz

from docflow.domains.ocr.models import ExtractResult, OcrResult
from docflow.domains.ocr.tesseract import get_tesseract_cmd, get_tesseract_env
from docflow.shared import ensure_directory, find_files


def has_text(pdf_path: Path | str, min_chars: int = 100) -> bool:
    """Return whether a PDF has enough extractable text."""
    try:
        doc = fitz.open(pdf_path)
        try:
            text = ""
            for page in doc:
                text += page.get_text()
                if len(text) >= min_chars:
                    return True
            return len(text.strip()) >= min_chars
        finally:
            doc.close()
    except Exception:
        return False


def ocr_pdf(
    pdf_path: Path | str,
    output_path: Path | None = None,
    skip_if_text: bool = True,
) -> OcrResult:
    """Run OCR on a single PDF file."""
    input_path = Path(pdf_path)
    if not input_path.exists():
        return OcrResult(input_path, success=False, skipped=False, message="File not found")

    if input_path.suffix.lower() != ".pdf":
        return OcrResult(input_path, success=False, skipped=False, message="Not a PDF file")

    if skip_if_text and has_text(input_path):
        return OcrResult(input_path, success=True, skipped=True, message="Already has text")

    in_place = output_path is None

    try:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            target_path = output_path or temp_dir / "output.pdf"
            doc = fitz.open(input_path)

            try:
                for page_num in range(len(doc)):
                    page = doc[page_num]

                    if skip_if_text and len(page.get_text().strip()) > 50:
                        continue

                    pix = page.get_pixmap(dpi=300)
                    img_path = temp_dir / f"page-{page_num}.png"
                    pix.save(str(img_path))

                    pdf_path_out = temp_dir / f"page-{page_num}-ocr"
                    result = subprocess.run(
                        [
                            get_tesseract_cmd(),
                            str(img_path),
                            str(pdf_path_out),
                            "-l",
                            "eng",
                            "pdf",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        env=get_tesseract_env(),
                    )

                    if result.returncode != 0:
                        error = result.stderr.strip() or "Tesseract failed"
                        return OcrResult(input_path, success=False, skipped=False, message=error)

                    ocr_pdf_path = pdf_path_out.with_suffix(".pdf")
                    if ocr_pdf_path.exists():
                        ocr_doc = fitz.open(ocr_pdf_path)
                        try:
                            ocr_page = ocr_doc[0]
                            text_page = ocr_page.get_textpage()
                            blocks = ocr_page.get_text("dict", textpage=text_page)["blocks"]

                            for block in blocks:
                                if block["type"] == 0:
                                    for line in block["lines"]:
                                        for span in line["spans"]:
                                            rect = fitz.Rect(span["bbox"])
                                            scale = page.rect.width / pix.width
                                            scaled_rect = rect * scale

                                            page.insert_textbox(
                                                scaled_rect,
                                                span["text"],
                                                fontsize=span["size"] * scale,
                                                render_mode=3,
                                            )
                        finally:
                            ocr_doc.close()

                doc.save(str(target_path))
            finally:
                doc.close()

            if in_place:
                shutil.move(str(target_path), str(input_path))

        return OcrResult(input_path, success=True, skipped=False, message="OCR completed")
    except subprocess.TimeoutExpired:
        return OcrResult(input_path, success=False, skipped=False, message="Timeout")
    except Exception as e:
        return OcrResult(input_path, success=False, skipped=False, message=str(e))


def extract_text(
    pdf_path: Path | str,
    output_path: Path | None = None,
    ocr_if_needed: bool = True,
) -> ExtractResult:
    """Extract text from a PDF, running OCR first if needed."""
    input_path = Path(pdf_path)
    if not input_path.exists():
        return ExtractResult(
            input_path, None, success=False, ocr_performed=False, message="File not found"
        )

    if output_path is None:
        output_path = input_path.with_suffix(".txt")

    try:
        doc = fitz.open(input_path)
        try:
            text = "".join(page.get_text() for page in doc)
        finally:
            doc.close()

        ocr_performed = False
        if len(text.strip()) < 100 and ocr_if_needed:
            ocr_result = ocr_pdf(input_path, skip_if_text=False)
            if not ocr_result.success:
                return ExtractResult(
                    input_path,
                    None,
                    success=False,
                    ocr_performed=False,
                    message=f"OCR failed: {ocr_result.message}",
                )

            ocr_performed = True
            doc = fitz.open(input_path)
            try:
                text = "".join(page.get_text() for page in doc)
            finally:
                doc.close()

        output_path.write_text(text.strip())

        if ocr_performed:
            return ExtractResult(input_path, output_path, True, True, "OCR'd and extracted")
        return ExtractResult(input_path, output_path, True, False, "Extracted existing text")
    except Exception as e:
        return ExtractResult(input_path, None, success=False, ocr_performed=False, message=str(e))


def find_pdfs(directory: Path | str, recursive: bool = True) -> list[Path]:
    """Find PDF files in a directory."""
    return find_files(directory, {".pdf"}, recursive=recursive)


def ocr_directory(
    directory: Path | str,
    recursive: bool = True,
    skip_if_text: bool = True,
    callback: Callable[[Path, int, int], None] | None = None,
) -> list[OcrResult]:
    """Run OCR on PDFs in a directory."""
    root = ensure_directory(directory)
    pdfs = find_pdfs(root, recursive)
    results = []

    for index, pdf_path in enumerate(pdfs):
        if callback:
            callback(pdf_path, index, len(pdfs))
        results.append(ocr_pdf(pdf_path, skip_if_text=skip_if_text))

    return results

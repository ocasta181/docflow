from pathlib import Path
import shutil

import fitz
from PIL import Image, ImageDraw
import pytest

from docflow.domains.ocr.models import ExtractResult, OcrResult
from docflow.domains.ocr.service import extract_text, find_pdfs, has_text, ocr_directory, ocr_pdf


def create_text_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This PDF has extractable text content. " * 10, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def create_image_pdf(path: Path) -> Path:
    image_path = path.with_suffix(".png")
    image = Image.new("RGB", (500, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 80), "SCANNED TEXT", fill="black")
    image.save(image_path)

    doc = fitz.open()
    page = doc.new_page(width=500, height=200)
    page.insert_image(page.rect, filename=str(image_path))
    doc.save(str(path))
    doc.close()
    image_path.unlink()
    return path


def test_has_text_detects_extractable_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    assert has_text(pdf_path)


def test_has_text_respects_min_chars_threshold(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    assert not has_text(pdf_path, min_chars=10_000)


def test_has_text_returns_false_for_missing_file(tmp_path: Path) -> None:
    assert not has_text(tmp_path / "missing.pdf")


def test_ocr_pdf_skips_pdf_with_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = ocr_pdf(pdf_path, skip_if_text=True)

    assert result.success
    assert result.skipped
    assert result.message == "Already has text"


def test_ocr_pdf_reports_missing_file(tmp_path: Path) -> None:
    result = ocr_pdf(tmp_path / "missing.pdf")

    assert not result.success
    assert not result.skipped
    assert "not found" in result.message.lower()


def test_ocr_pdf_reports_clear_error_when_tesseract_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = create_image_pdf(tmp_path / "scan.pdf")
    monkeypatch.setattr(
        "docflow.domains.ocr.service.tesseract_unavailable_message",
        lambda: "Tesseract executable not found. Install Tesseract and ensure it is on PATH.",
    )

    result = ocr_pdf(pdf_path, skip_if_text=True)

    assert not result.success
    assert not result.skipped
    assert result.message.startswith("Tesseract executable not found")


def test_ocr_pdf_skips_text_pdf_without_tesseract_preflight(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    def fail_preflight() -> str | None:
        raise AssertionError("Tesseract should not be checked for skipped text PDFs")

    monkeypatch.setattr("docflow.domains.ocr.service.tesseract_unavailable_message", fail_preflight)

    result = ocr_pdf(pdf_path, skip_if_text=True)

    assert result.success
    assert result.skipped


def test_ocr_pdf_rejects_non_pdf_file(tmp_path: Path) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("hello")

    result = ocr_pdf(text_file)

    assert not result.success
    assert not result.skipped
    assert result.message == "Not a PDF file"


def test_ocr_pdf_rejects_output_matching_input(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = ocr_pdf(pdf_path, output_path=pdf_path)

    assert not result.success
    assert not result.skipped
    assert "different from input" in result.message


def test_ocr_pdf_rejects_non_pdf_output_path(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = ocr_pdf(pdf_path, output_path=tmp_path / "ocr.txt")

    assert not result.success
    assert not result.skipped
    assert "Output must have extension: .pdf" in result.message


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_ocr_pdf_can_write_custom_output_for_scanned_pdf(tmp_path: Path) -> None:
    pdf_path = create_image_pdf(tmp_path / "scan.pdf")
    output_path = tmp_path / "ocr.pdf"

    result = ocr_pdf(pdf_path, output_path=output_path, skip_if_text=True)

    assert result.success
    assert not result.skipped
    assert output_path.exists()
    assert pdf_path.exists()


def test_extract_text_writes_existing_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = extract_text(pdf_path)

    assert result.success
    assert not result.ocr_performed
    assert result.output_path == pdf_path.with_suffix(".txt")
    assert "extractable text" in result.output_path.read_text()


def test_extract_text_respects_custom_output_path(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")
    output_path = tmp_path / "custom.txt"

    result = extract_text(pdf_path, output_path=output_path)

    assert result.success
    assert result.output_path == output_path
    assert output_path.exists()


def test_extract_text_reports_missing_file(tmp_path: Path) -> None:
    result = extract_text(tmp_path / "missing.pdf")

    assert not result.success
    assert not result.ocr_performed
    assert "not found" in result.message.lower()


def test_extract_text_returns_result_model(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    assert isinstance(extract_text(pdf_path), ExtractResult)


def test_find_pdfs_respects_recursive_flag(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    root_pdf = create_text_pdf(tmp_path / "root.pdf")
    create_text_pdf(nested / "nested.pdf")

    assert find_pdfs(tmp_path, recursive=False) == [root_pdf.resolve()]


def test_ocr_directory_processes_matching_pdfs(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    create_text_pdf(tmp_path / "root.pdf")
    create_text_pdf(nested / "nested.pdf")

    results = ocr_directory(tmp_path, recursive=True)

    assert len(results) == 2
    assert all(isinstance(result, OcrResult) for result in results)


def test_ocr_directory_respects_non_recursive_mode(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    create_text_pdf(tmp_path / "root.pdf")
    create_text_pdf(nested / "nested.pdf")

    results = ocr_directory(tmp_path, recursive=False)

    assert len(results) == 1


def test_ocr_directory_reports_progress_with_zero_based_index(tmp_path: Path) -> None:
    create_text_pdf(tmp_path / "first.pdf")
    create_text_pdf(tmp_path / "second.pdf")
    calls = []

    def record(path: Path, index: int, total: int) -> None:
        calls.append((path.name, index, total))

    ocr_directory(tmp_path, callback=record)

    assert calls == [("first.pdf", 0, 2), ("second.pdf", 1, 2)]

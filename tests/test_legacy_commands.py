from pathlib import Path

import fitz
from PIL import Image
from pypdf import PdfReader, PdfWriter

from docflow_cli.legacy import batch_ocr, jpg2pdf, pdftools


def create_pdf(path: Path, page_count: int = 1) -> Path:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as file:
        writer.write(file)
    return path


def create_text_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This PDF has extractable text content. " * 10, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def create_jpeg(path: Path) -> None:
    image = Image.new("RGB", (200, 300), (255, 0, 0))
    image.save(path, "JPEG")


def test_pdftools_legacy_wrapper_routes_pdf_commands(tmp_path: Path) -> None:
    input_pdf = create_pdf(tmp_path / "input.pdf", 2)

    result = pdftools.main(["reverse", str(input_pdf)])

    assert result == 0
    assert (tmp_path / "input_reversed.pdf").exists()


def test_jpg2pdf_legacy_wrapper_routes_image_command(tmp_path: Path) -> None:
    create_jpeg(tmp_path / "scan_1.jpg")
    output_dir = tmp_path / "pdfs"

    result = jpg2pdf.main([str(tmp_path), "--output", str(output_dir)])

    assert result == 0
    assert len(PdfReader(output_dir / "scan.pdf").pages) == 1


def test_batch_ocr_legacy_wrapper_routes_run_command(tmp_path: Path, capsys) -> None:
    input_pdf = create_text_pdf(tmp_path / "input.pdf")

    result = batch_ocr.main([str(input_pdf)])

    assert result == 0
    captured = capsys.readouterr()
    assert "Skipped: Already has text" in captured.out


def test_batch_ocr_legacy_wrapper_routes_extract_flag(tmp_path: Path) -> None:
    input_pdf = create_text_pdf(tmp_path / "input.pdf")

    result = batch_ocr.main(["--extract", str(input_pdf)])

    assert result == 0
    assert input_pdf.with_suffix(".txt").exists()


def test_batch_ocr_legacy_extract_ignores_force_flag(tmp_path: Path) -> None:
    input_pdf = create_text_pdf(tmp_path / "input.pdf")

    result = batch_ocr.main(["--extract", "--force", str(input_pdf)])

    assert result == 0
    assert input_pdf.with_suffix(".txt").exists()


def test_batch_ocr_legacy_help_lists_extract_flag(capsys) -> None:
    result = batch_ocr.main(["--help"])

    assert result == 0
    captured = capsys.readouterr()
    assert "--extract" in captured.out

from pathlib import Path

import fitz

from docflow.cli.app import main


def create_text_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This PDF has extractable text content. " * 10, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_docflow_ocr_run_skips_pdf_with_text(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(pdf_path)])

    assert result == 0
    captured = capsys.readouterr()
    assert "Skipped: Already has text" in captured.out


def test_docflow_ocr_extract_writes_text_file(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "extract", str(pdf_path)])

    assert result == 0
    assert pdf_path.with_suffix(".txt").exists()
    captured = capsys.readouterr()
    assert "extracted" in captured.out


def test_docflow_ocr_run_dry_run_directory(tmp_path: Path, capsys) -> None:
    create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(tmp_path), "--dry-run"])

    assert result == 0
    captured = capsys.readouterr()
    assert "Found 1 PDF" in captured.out


def test_docflow_ocr_reports_missing_path(tmp_path: Path, capsys) -> None:
    result = main(["ocr", "run", str(tmp_path / "missing")])

    assert result == 1
    captured = capsys.readouterr()
    assert "Path not found" in captured.err

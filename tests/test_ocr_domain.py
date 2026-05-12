from pathlib import Path

import fitz

from docflow.domains.ocr.service import extract_text, find_pdfs, has_text, ocr_pdf


def create_text_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This PDF has extractable text content. " * 10, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_has_text_detects_extractable_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    assert has_text(pdf_path)


def test_ocr_pdf_skips_pdf_with_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = ocr_pdf(pdf_path, skip_if_text=True)

    assert result.success
    assert result.skipped
    assert result.message == "Already has text"


def test_extract_text_writes_existing_text(tmp_path: Path) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = extract_text(pdf_path)

    assert result.success
    assert not result.ocr_performed
    assert result.output_path == pdf_path.with_suffix(".txt")
    assert "extractable text" in result.output_path.read_text()


def test_find_pdfs_respects_recursive_flag(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    root_pdf = create_text_pdf(tmp_path / "root.pdf")
    create_text_pdf(nested / "nested.pdf")

    assert find_pdfs(tmp_path, recursive=False) == [root_pdf.resolve()]

import json
from pathlib import Path

import fitz

from pliage.cli.app import main


def create_text_pdf(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This PDF has extractable text content. " * 10, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_pliage_ocr_run_skips_pdf_with_text(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(pdf_path)])

    assert result == 0
    captured = capsys.readouterr()
    assert "Skipped: Already has text" in captured.out


def test_pliage_ocr_run_json_skips_pdf_with_text(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(pdf_path), "--json"])

    assert result == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "command": "ocr run",
        "result": {
            "message": "Already has text",
            "output_path": None,
            "path": str(pdf_path),
            "skipped": True,
            "success": True,
        },
        "success": True,
    }


def test_pliage_ocr_extract_writes_text_file(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "extract", str(pdf_path)])

    assert result == 0
    assert pdf_path.with_suffix(".txt").exists()
    captured = capsys.readouterr()
    assert "extracted" in captured.out


def test_pliage_ocr_run_dry_run_directory(tmp_path: Path, capsys) -> None:
    create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(tmp_path), "--dry-run"])

    assert result == 0
    captured = capsys.readouterr()
    assert "Found 1 PDF" in captured.out


def test_pliage_ocr_run_help_lists_language_option(capsys) -> None:
    result = main(["ocr", "run", "--help"])

    assert result == 0
    captured = capsys.readouterr()
    assert "--lang" in captured.out


def test_pliage_ocr_extract_help_lists_language_option(capsys) -> None:
    result = main(["ocr", "extract", "--help"])

    assert result == 0
    captured = capsys.readouterr()
    assert "--lang" in captured.out


def test_pliage_ocr_run_dry_run_single_file_shows_output(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")
    output_path = tmp_path / "ocr.pdf"

    result = main(["ocr", "run", str(pdf_path), "--dry-run", "--output", str(output_path)])

    assert result == 0
    captured = capsys.readouterr()
    assert f"{pdf_path} -> {output_path}" in captured.out


def test_pliage_ocr_run_dry_run_directory_shows_output_dir(tmp_path: Path, capsys) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    create_text_pdf(nested / "text.pdf")
    output_dir = tmp_path / "ocr-output"

    result = main(["ocr", "run", str(tmp_path), "--dry-run", "--output-dir", str(output_dir)])

    assert result == 0
    captured = capsys.readouterr()
    assert f"nested/text.pdf -> {output_dir / 'nested' / 'text.pdf'}" in captured.out


def test_pliage_ocr_run_rejects_output_for_directory(tmp_path: Path, capsys) -> None:
    create_text_pdf(tmp_path / "text.pdf")

    result = main(["ocr", "run", str(tmp_path), "--output", str(tmp_path / "ocr.pdf")])

    assert result == 1
    captured = capsys.readouterr()
    assert "--output can only be used with a single PDF file" in captured.err


def test_pliage_ocr_run_rejects_conflicting_output_options(tmp_path: Path, capsys) -> None:
    pdf_path = create_text_pdf(tmp_path / "text.pdf")

    result = main(
        [
            "ocr",
            "run",
            str(pdf_path),
            "--output",
            str(tmp_path / "ocr.pdf"),
            "--output-dir",
            str(tmp_path / "ocr-output"),
        ]
    )

    assert result == 1
    captured = capsys.readouterr()
    assert "Use either --output or --output-dir" in captured.err


def test_pliage_ocr_reports_missing_path(tmp_path: Path, capsys) -> None:
    result = main(["ocr", "run", str(tmp_path / "missing")])

    assert result == 1
    captured = capsys.readouterr()
    assert "Path not found" in captured.err


def test_pliage_ocr_json_reports_missing_path(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing"

    result = main(["ocr", "run", str(missing_path), "--json"])

    assert result == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"error": f"Path not found: {missing_path.resolve()}", "success": False}
    assert captured.err == ""

from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from pliage.domains.image_pdf.service import (
    create_pdf,
    create_pdfs_from_directory,
    parse_filename,
    scan_directory,
)


def create_test_jpeg(path: Path, color: tuple[int, int, int] = (255, 0, 0)) -> None:
    image = Image.new("RGB", (200, 300), color)
    image.save(path, "JPEG")


def test_create_pdfs_from_directory_groups_by_prefix(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "invoice_1.jpg")
    create_test_jpeg(tmp_path / "invoice_2.jpg")
    create_test_jpeg(tmp_path / "receipt_1.jpg")
    output_dir = tmp_path / "pdfs"

    results, warnings = create_pdfs_from_directory(tmp_path, output_dir)

    assert [result.prefix for result in results] == ["invoice", "receipt"]
    assert (output_dir / "invoice.pdf").exists()
    assert (output_dir / "receipt.pdf").exists()
    assert len(PdfReader(output_dir / "invoice.pdf").pages) == 2
    assert warnings == []


def test_create_pdfs_from_directory_filters_prefix(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "invoice_1.jpg")
    create_test_jpeg(tmp_path / "receipt_1.jpg")
    output_dir = tmp_path / "pdfs"

    results, _ = create_pdfs_from_directory(tmp_path, output_dir, prefix_filter="invoice")

    assert [result.prefix for result in results] == ["invoice"]
    assert (output_dir / "invoice.pdf").exists()
    assert not (output_dir / "receipt.pdf").exists()


def test_create_pdfs_from_directory_warns_on_sequence_gaps(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "doc_1.jpg")
    create_test_jpeg(tmp_path / "doc_3.jpg")

    _, warnings = create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

    assert any("missing sequence number" in warning for warning in warnings)


def test_create_pdfs_from_directory_groups_case_insensitively(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "Tax_1.jpg")
    create_test_jpeg(tmp_path / "tax_2.jpg")
    create_test_jpeg(tmp_path / "TAX_3.jpg")
    output_dir = tmp_path / "pdfs"

    results, warnings = create_pdfs_from_directory(tmp_path, output_dir)

    assert [result.prefix.lower() for result in results] == ["tax"]
    assert len(PdfReader(next(output_dir.glob("*.pdf"))).pages) == 3
    assert warnings == []


def test_create_pdfs_from_directory_accepts_jpeg_extension_variants(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "doc_1.jpg")
    create_test_jpeg(tmp_path / "doc_2.jpeg")
    create_test_jpeg(tmp_path / "doc_3.JPG")
    create_test_jpeg(tmp_path / "doc_4.JPEG")

    results, _ = create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

    assert [result.image_count for result in results] == [4]
    assert len(PdfReader(tmp_path / "pdfs" / "doc.pdf").pages) == 4


def test_create_pdfs_from_directory_keeps_numbers_inside_prefix(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "Bank_statement_july_2023_1.jpg")
    create_test_jpeg(tmp_path / "Bank_statement_july_2023_2.jpg")

    results, _ = create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

    assert [result.prefix for result in results] == ["Bank_statement_july_2023"]
    assert (tmp_path / "pdfs" / "Bank_statement_july_2023.pdf").exists()


def test_create_pdfs_from_directory_rejects_empty_input(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "random.jpg")

    with pytest.raises(ValueError, match="No valid files"):
        create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")


def test_parse_filename_uses_final_number_as_sequence() -> None:
    assert parse_filename("Bank_statement_july_2023_12.JPEG") == (
        "Bank_statement_july_2023",
        12,
    )


def test_scan_directory_warns_for_non_matching_files(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "doc_1.jpg")
    create_test_jpeg(tmp_path / "random.jpg")
    (tmp_path / "notes.txt").write_text("hello")

    groups, warnings = scan_directory(tmp_path)

    assert list(groups) == ["doc"]
    assert warnings == [
        "Skipping: notes.txt (doesn't match pattern)",
        "Skipping: random.jpg (doesn't match pattern)",
    ]


def test_create_pdf_does_not_flatten_unexpected_errors(tmp_path: Path, monkeypatch) -> None:
    image_path = tmp_path / "doc_1.jpg"
    create_test_jpeg(image_path)

    def fail_unexpectedly(*_args, **_kwargs):
        raise AssertionError("unexpected bug")

    monkeypatch.setattr("pliage.domains.image_pdf.service.Image.open", fail_unexpectedly)

    with pytest.raises(AssertionError, match="unexpected bug"):
        create_pdf([(1, image_path)], tmp_path / "doc.pdf")

from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

from docflow.domains.image_pdf.service import create_pdfs_from_directory


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


def test_create_pdfs_from_directory_rejects_empty_input(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "random.jpg")

    with pytest.raises(ValueError, match="No valid files"):
        create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

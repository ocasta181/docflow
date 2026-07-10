from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader

from pliage.domains.image_pdf.service import (
    convert_to_grayscale,
    create_pdf,
    create_pdfs_from_directory,
    detect_grid_pitch,
    page_height_in_pixels,
    parse_filename,
    parse_grid_size_cm,
    scan_directory,
    split_at_whitespace,
)


def create_grid_image(path: Path, pitch: int, size: tuple[int, int] = (900, 700)) -> None:
    """Write a PNG of graph paper with square cells *pitch* pixels across."""
    image = Image.new("L", size, 245)
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], pitch):
        draw.line([(x, 0), (x, size[1])], fill=60, width=2)
    for y in range(0, size[1], pitch):
        draw.line([(0, y), (size[0], y)], fill=60, width=2)
    image.save(path, "PNG")


def create_test_jpeg(path: Path, color: tuple[int, int, int] = (255, 0, 0)) -> None:
    image = Image.new("RGB", (200, 250), color)
    image.save(path, "JPEG")


def create_test_png(
    path: Path,
    color: tuple[int, int, int, int] = (0, 128, 0, 255),
) -> None:
    image = Image.new("RGBA", (200, 250), color)
    image.save(path, "PNG")


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


def test_create_pdfs_from_directory_accepts_png_files(tmp_path: Path) -> None:
    create_test_png(tmp_path / "letter_1.png")
    create_test_png(tmp_path / "letter_2.PNG")
    output_dir = tmp_path / "pdfs"

    results, warnings = create_pdfs_from_directory(tmp_path, output_dir)

    assert [result.image_count for result in results] == [2]
    assert len(PdfReader(output_dir / "letter.pdf").pages) == 2
    assert warnings == []


def test_create_pdfs_from_directory_mixes_jpeg_and_png(tmp_path: Path) -> None:
    create_test_jpeg(tmp_path / "scan_1.jpg")
    create_test_png(tmp_path / "scan_2.png")

    results, _ = create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

    assert [result.image_count for result in results] == [2]


def test_create_pdfs_from_directory_flattens_png_transparency(tmp_path: Path) -> None:
    create_test_png(tmp_path / "doc_1.png", color=(0, 0, 0, 0))

    results, warnings = create_pdfs_from_directory(tmp_path, tmp_path / "pdfs")

    assert [result.image_count for result in results] == [1]
    assert warnings == []


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


def test_create_pdf_paginates_image_taller_than_page(tmp_path: Path) -> None:
    image_path = tmp_path / "tall_1.jpg"
    Image.new("RGB", (200, 800), (255, 255, 255)).save(image_path, "JPEG")

    create_pdf([(1, image_path)], tmp_path / "tall.pdf")

    pages = PdfReader(tmp_path / "tall.pdf").pages
    page_h_px = page_height_in_pixels(200)
    expected = -(-800 // page_h_px)
    assert len(pages) == expected
    assert expected > 1


def test_split_at_whitespace_cuts_at_bright_band() -> None:
    img = Image.new("L", (100, 600), 0)
    page_h = page_height_in_pixels(100)
    search_window = max(1, int(page_h * 0.15))
    band_start = page_h - search_window + 2
    band_end = page_h - 2
    ImageDraw.Draw(img).rectangle([0, band_start, 99, band_end], fill=255)

    slices = list(split_at_whitespace(img, page_h))

    assert slices[0].height == band_end + 1


def test_split_at_whitespace_returns_single_slice_when_image_fits() -> None:
    img = Image.new("L", (100, 50), 255)
    slices = list(split_at_whitespace(img, page_height_in_pixels(100)))
    assert len(slices) == 1
    assert slices[0].height == 50


def test_create_pdf_does_not_flatten_unexpected_errors(tmp_path: Path, monkeypatch) -> None:
    image_path = tmp_path / "doc_1.jpg"
    create_test_jpeg(image_path)

    def fail_unexpectedly(*_args, **_kwargs):
        raise AssertionError("unexpected bug")

    monkeypatch.setattr("pliage.domains.image_pdf.service.Image.open", fail_unexpectedly)

    with pytest.raises(AssertionError, match="unexpected bug"):
        create_pdf([(1, image_path)], tmp_path / "doc.pdf")


def test_parse_grid_size_cm_units() -> None:
    assert parse_grid_size_cm("1cm") == pytest.approx(1.0)
    assert parse_grid_size_cm("5mm") == pytest.approx(0.5)
    assert parse_grid_size_cm("0.5in") == pytest.approx(1.27)
    with pytest.raises(ValueError):
        parse_grid_size_cm("banana")


def test_detect_grid_pitch_recovers_known_pitch(tmp_path: Path) -> None:
    grid_path = tmp_path / "grid.png"
    create_grid_image(grid_path, pitch=40)
    pitch = detect_grid_pitch(Image.open(grid_path))
    assert pitch is not None
    assert pitch == pytest.approx(40, abs=2)


def test_detect_grid_pitch_returns_none_without_grid(tmp_path: Path) -> None:
    blank = tmp_path / "blank.png"
    Image.new("L", (900, 700), 245).save(blank, "PNG")
    assert detect_grid_pitch(Image.open(blank)) is None


def test_convert_to_grayscale_detect_size_downscales(tmp_path: Path) -> None:
    # 40 px per 1 cm square => ~102 PPI; target 51 PPI should halve the image.
    create_grid_image(tmp_path / "note_1.png", pitch=40, size=(800, 600))
    converted, _ = convert_to_grayscale(
        tmp_path, dpi=51, detect_size=True, grid_size_cm=1.0
    )
    assert len(converted) == 1
    with Image.open(converted[0]) as out:
        assert out.width == pytest.approx(400, abs=15)
        assert out.height == pytest.approx(300, abs=15)


def test_convert_to_grayscale_detect_size_skips_undetected(tmp_path: Path) -> None:
    Image.new("L", (800, 600), 245).save(tmp_path / "blank_1.png", "PNG")
    converted, warnings = convert_to_grayscale(
        tmp_path, dpi=51, detect_size=True, grid_size_cm=1.0
    )
    assert len(converted) == 1
    with Image.open(converted[0]) as out:
        assert out.size == (800, 600)  # left unchanged
    assert any("no grid detected" in w for w in warnings)

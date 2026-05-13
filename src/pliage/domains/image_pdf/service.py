"""Image-to-PDF conversion service."""

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
import os
import re
import tempfile

from PIL import Image, UnidentifiedImageError
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from pliage.domains.image_pdf.models import ImagePdfResult
from pliage.shared import ensure_directory


PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 0.5 * inch
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
CONTENT_HEIGHT = PAGE_HEIGHT - 2 * MARGIN
WHITESPACE_SEARCH_FRACTION = 0.15
IMAGE_READ_ERRORS = (OSError, UnidentifiedImageError, ValueError)
EXIF_ORIENTATION_ERRORS = (AttributeError, KeyError, TypeError, ValueError)


def create_pdfs_from_directory(
    directory: Path | str,
    output_dir: Path | str,
    prefix_filter: str | None = None,
) -> tuple[list[ImagePdfResult], list[str]]:
    """Create PDFs from grouped sequential JPEG files in a directory."""
    input_dir = ensure_directory(directory)
    groups, warnings = scan_directory(input_dir, prefix_filter)
    if not groups:
        raise ValueError("No valid files found")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results: list[ImagePdfResult] = []
    for prefix, files in groups.items():
        missing = find_sequence_gaps(files)
        if missing:
            warnings.append(f'Warning: missing sequence number(s) {missing} in group "{prefix}"')

        pdf_path = output_path / f"{prefix}.pdf"
        created, create_warnings = create_pdf(files, pdf_path)
        warnings.extend(create_warnings)
        if created:
            results.append(ImagePdfResult(prefix, pdf_path, len(files)))
        else:
            warnings.append(f"Error: No valid images in group '{prefix}'")

    if not results:
        raise ValueError("No PDFs were created")

    return results, warnings


def parse_filename(filename: str) -> tuple[str, int] | None:
    """Parse '<prefix>_<number>.<ext>' filenames for supported image types."""
    match = re.match(r"^(.+)_(\d+)\.(?:jpe?g|png)$", filename, re.IGNORECASE)
    if match:
        prefix = match.group(1)
        sequence = int(match.group(2))
        return prefix, sequence
    return None


def scan_directory(
    directory: Path,
    prefix_filter: str | None = None,
) -> tuple[dict[str, list[tuple[int, Path]]], list[str]]:
    """Scan a directory for grouped JPEG files."""
    groups: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    original_case: dict[str, str] = {}
    warnings: list[str] = []

    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue

        parsed = parse_filename(entry.name)
        if parsed is None:
            warnings.append(f"Skipping: {entry.name} (doesn't match pattern)")
            continue

        prefix, sequence = parsed
        prefix_lower = prefix.lower()

        if prefix_filter and prefix_lower != prefix_filter.lower():
            continue

        if prefix_lower not in original_case:
            original_case[prefix_lower] = prefix

        groups[prefix_lower].append((sequence, entry))

    result = {}
    for prefix_lower, files in groups.items():
        result[original_case[prefix_lower]] = files

    return result, warnings


def find_sequence_gaps(files: list[tuple[int, Path]]) -> list[int]:
    """Return missing sequence numbers for a group of numbered files."""
    sequences = sorted(seq for seq, _ in files)
    if not sequences:
        return []

    expected = set(range(min(sequences), max(sequences) + 1))
    actual = set(sequences)
    return sorted(expected - actual)


def flatten_to_rgb(img: Image.Image) -> Image.Image:
    """Return an RGB image, compositing any alpha channel onto white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if img.mode in ("RGB", "L"):
        return img
    return img.convert("RGB")


def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """Apply EXIF orientation to image."""
    try:
        from PIL import ExifTags

        exif = img.getexif()
        if exif:
            orientation_tag = None
            for tag, name in ExifTags.TAGS.items():
                if name == "Orientation":
                    orientation_tag = tag
                    break

            if orientation_tag and orientation_tag in exif:
                orientation = exif[orientation_tag]

                if orientation == 2:
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 4:
                    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                elif orientation == 5:
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(90, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 7:
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
    except EXIF_ORIENTATION_ERRORS:
        pass

    return img


def page_height_in_pixels(image_width: int) -> int:
    """Image-pixel height that maps to one content page at scale-to-width."""
    return max(1, int(image_width * CONTENT_HEIGHT / CONTENT_WIDTH))


def split_at_whitespace(img: Image.Image, page_height_px: int) -> Iterator[Image.Image]:
    """Yield img slices ~page_height_px tall, cutting at the brightest row near each boundary."""
    if img.height <= page_height_px:
        yield img
        return

    gray = img.convert("L")
    row_strip = gray.resize((1, img.height), Image.Resampling.BOX)
    brightness = row_strip.tobytes()
    search_window = max(1, int(page_height_px * WHITESPACE_SEARCH_FRACTION))

    y = 0
    while y < img.height:
        ideal_end = y + page_height_px
        if ideal_end >= img.height:
            cut = img.height
        else:
            start = max(y + 1, ideal_end - search_window)
            window = brightness[start:ideal_end]
            best_offset = 0
            best_brightness = -1
            for i, value in enumerate(window):
                if value >= best_brightness:
                    best_brightness = value
                    best_offset = i
            cut = start + best_offset + 1
        yield img.crop((0, y, img.width, cut))
        y = cut


def draw_image_paginated(pdf_canvas: canvas.Canvas, img: Image.Image) -> int:
    """Draw img across one or more pages, splitting on whitespace when too tall."""
    pts_per_pixel = CONTENT_WIDTH / img.width
    page_height_px = page_height_in_pixels(img.width)
    pages = 0
    for slice_img in split_at_whitespace(img, page_height_px):
        slice_h_pts = slice_img.height * pts_per_pixel
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
            slice_img.save(tmp_path, "JPEG", quality=95)
        try:
            top_y = PAGE_HEIGHT - MARGIN - slice_h_pts
            pdf_canvas.drawImage(tmp_path, MARGIN, top_y, width=CONTENT_WIDTH, height=slice_h_pts)
            pdf_canvas.showPage()
            pages += 1
        finally:
            os.unlink(tmp_path)
    return pages


def create_pdf(files: list[tuple[int, Path]], output_path: Path) -> tuple[bool, list[str]]:
    """Create one PDF from a list of numbered image files."""
    sorted_files = sorted(files, key=lambda item: item[0])
    pdf_canvas = canvas.Canvas(str(output_path), pagesize=LETTER)
    pages_added = 0
    warnings: list[str] = []

    for _, file_path in sorted_files:
        try:
            img = Image.open(file_path)
            img = apply_exif_orientation(img)
            img = flatten_to_rgb(img)
            pages_added += draw_image_paginated(pdf_canvas, img)
        except IMAGE_READ_ERRORS as e:
            warnings.append(f"Warning: Could not process {file_path.name}: {e}")
            continue

    if pages_added > 0:
        pdf_canvas.save()
        return True, warnings

    return False, warnings

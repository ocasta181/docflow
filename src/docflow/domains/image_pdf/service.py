"""Image-to-PDF conversion service."""

from collections import defaultdict
from pathlib import Path
import os
import re
import tempfile

from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from docflow.domains.image_pdf.models import ImagePdfResult
from docflow.shared import ensure_directory


PAGE_WIDTH, PAGE_HEIGHT = LETTER


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
    """Parse '<prefix>_<number>.jpg' filenames."""
    match = re.match(r"^(.+)_(\d+)\.jpe?g$", filename, re.IGNORECASE)
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
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 4:
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                elif orientation == 5:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 7:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
    except Exception:
        pass

    return img


def calculate_image_size(img_width: int, img_height: int) -> tuple[float, float, float, float]:
    """
    Calculate the size and position to fit image on US Letter page.
    Returns (x, y, width, height) in points.
    """
    margin = 0.5 * inch
    max_width = PAGE_WIDTH - 2 * margin
    max_height = PAGE_HEIGHT - 2 * margin

    scale_w = max_width / img_width
    scale_h = max_height / img_height
    scale = min(scale_w, scale_h)

    new_width = img_width * scale
    new_height = img_height * scale

    x = (PAGE_WIDTH - new_width) / 2
    y = (PAGE_HEIGHT - new_height) / 2

    return x, y, new_width, new_height


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

            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, "JPEG", quality=95)

            try:
                x, y, width, height = calculate_image_size(img.width, img.height)
                pdf_canvas.drawImage(tmp_path, x, y, width=width, height=height)
                pdf_canvas.showPage()
                pages_added += 1
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            warnings.append(f"Warning: Could not process {file_path.name}: {e}")
            continue

    if pages_added > 0:
        pdf_canvas.save()
        return True, warnings

    return False, warnings

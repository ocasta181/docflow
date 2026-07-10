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


def convert_to_grayscale(
    directory: Path | str,
    output_dir: Path | str | None = None,
    dpi: int | None = None,
    detect_size: bool = False,
    grid_size_cm: float | None = None,
) -> tuple[list[Path], list[str]]:
    """Convert all supported images in *directory* to grayscale PNGs.

    If *output_dir* is ``None`` the files are overwritten in-place (as PNG).

    If *dpi* is given, images are resampled to that target resolution:

    * When *detect_size* is true, the true resolution is measured from a
      reference grid whose squares are *grid_size_cm* centimeters across
      (see :func:`detect_grid_pitch`).  Images whose grid can't be detected
      are left unchanged and a warning is recorded.
    * Otherwise the legacy 8.5x11 page assumption is used.

    Returns a list of output paths and a list of warning strings.
    """
    input_dir = ensure_directory(directory)
    out_dir = Path(output_dir) if output_dir is not None else input_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    supported = re.compile(r"\.(?:jpe?g|png|heic|heif|tiff?|webp|bmp)$", re.IGNORECASE)
    converted: list[Path] = []
    warnings: list[str] = []

    for entry in sorted(input_dir.iterdir()):
        if not entry.is_file() or not supported.search(entry.name):
            continue
        try:
            img = Image.open(entry)
            img = apply_exif_orientation(img)
            gray = img.convert("L")

            save_dpi = dpi if dpi is not None else 72
            if dpi is not None and detect_size:
                gray, applied, note = _resample_by_grid(gray, dpi, grid_size_cm or 1.0, entry.name)
                if note:
                    warnings.append(note)
                if applied is None:
                    save_dpi = 72
            elif dpi is not None:
                gray = _resample_to_dpi(gray, dpi)

            dest = out_dir / f"{entry.stem}.png"
            gray.save(dest, "PNG", dpi=(save_dpi, save_dpi))
            converted.append(dest)
        except IMAGE_READ_ERRORS as e:
            warnings.append(f"Warning: Could not process {entry.name}: {e}")

    if not converted:
        raise ValueError("No images were converted")

    return converted, warnings


CM_PER_INCH = 2.54

# Grid-pitch search bounds (pixels per square) in the projection sample space.
_GRID_PITCH_LO = 25
_GRID_PITCH_HI = 260
# Cap projection length so the pure-Python autocorrelation stays fast; the
# measured pitch is scaled back to full resolution afterwards.
_MAX_PROJECTION = 1500
# Squares are square: the two axes' pitches must agree within this fraction.
_AXIS_AGREEMENT_TOL = 0.08

_GRID_SIZE_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*(cm|mm|in|inch|\")\s*$", re.IGNORECASE)


def parse_grid_size_cm(spec: str) -> float:
    """Parse a physical grid-square size like '1cm', '5mm', '0.5in' into centimeters."""
    match = _GRID_SIZE_RE.match(spec)
    if not match:
        raise ValueError(f"Invalid grid size {spec!r}; use e.g. '1cm', '5mm', '0.5in'")
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "mm":
        return value / 10.0
    if unit in ("in", "inch", '"'):
        return value * CM_PER_INCH
    return value


def _darkness_projection(gray: Image.Image, axis: int) -> tuple[list[float], int]:
    """Return a 1-D darkness profile along *axis* and the full-res length it spans.

    axis 0 collapses width to find horizontal lines (profile down the height);
    axis 1 collapses height to find vertical lines (profile across the width).
    PIL box-resize does the averaging, avoiding a numpy dependency.
    """
    if axis == 0:
        length = gray.height
        size = (1, min(length, _MAX_PROJECTION))
    else:
        length = gray.width
        size = (min(length, _MAX_PROJECTION), 1)
    strip = gray.resize(size, Image.Resampling.BOX)
    return [255.0 - value for value in strip.tobytes()], length


def _autocorr_pitch(values: list[float], max_lag: int) -> tuple[float, float] | None:
    """Return (pitch, peak strength) via an autocorrelation peak-comb, or None.

    The fundamental is the strongest autocorrelation peak in the plausible band;
    higher harmonics are divided down to their order and combined, which avoids
    locking onto a half-pitch.
    """
    n = len(values)
    if n < _GRID_PITCH_LO * 2:
        return None
    mean = sum(values) / n
    x = [v - mean for v in values]
    energy = sum(v * v for v in x)
    if energy <= 0:
        return None

    max_lag = min(max_lag, n - 1)
    ac = [0.0] * (max_lag + 1)
    for lag in range(1, max_lag + 1):
        total = 0.0
        for i in range(n - lag):
            total += x[i] * x[i + lag]
        ac[lag] = total / energy

    peaks = [
        i
        for i in range(max(_GRID_PITCH_LO, 1), max_lag)
        if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > 0.05
    ]
    candidates = [p for p in peaks if _GRID_PITCH_LO <= p <= _GRID_PITCH_HI]
    if not candidates:
        return None
    fundamental = max(candidates, key=lambda p: ac[p])

    estimates = []
    for p in peaks:
        order = round(p / fundamental)
        if order >= 1 and abs(p - order * fundamental) < 0.15 * fundamental:
            estimates.append(p / order)
    estimates.sort()
    pitch = estimates[len(estimates) // 2] if estimates else float(fundamental)
    return pitch, ac[fundamental]


def detect_grid_pitch(gray: Image.Image) -> float | None:
    """Detect graph-paper grid pitch in pixels per square, or None if undetected.

    Measures the period independently along both axes and cross-checks them
    (the squares are square): returns the average when they agree within
    :data:`_AXIS_AGREEMENT_TOL`, the stronger axis when they don't, and None
    when no reliable grid is found on either axis.
    """
    results: list[tuple[float, float]] = []
    for axis in (0, 1):
        values, length = _darkness_projection(gray, axis)
        scale = length / len(values)
        hit = _autocorr_pitch(values, max_lag=4 * _GRID_PITCH_HI)
        if hit is not None:
            pitch, strength = hit
            results.append((pitch * scale, strength))

    if not results:
        return None
    if len(results) == 1:
        return results[0][0]

    (p0, s0), (p1, s1) = results
    if abs(p0 - p1) / max(p0, p1) <= _AXIS_AGREEMENT_TOL:
        return (p0 + p1) / 2
    return p0 if s0 >= s1 else p1


def _resample_by_grid(
    gray: Image.Image,
    target_dpi: int,
    grid_size_cm: float,
    name: str,
) -> tuple[Image.Image, int | None, str | None]:
    """Downscale *gray* to *target_dpi* using a detected reference grid.

    Returns (image, applied_dpi, note).  When the grid can't be detected the
    image is returned unchanged with ``applied_dpi=None`` and a warning note.
    """
    pitch = detect_grid_pitch(gray)
    if pitch is None:
        return gray, None, f"Warning: no grid detected in {name}; left unchanged"

    true_ppi = (pitch / grid_size_cm) * CM_PER_INCH
    scale = target_dpi / true_ppi
    if scale >= 1.0:
        note = (
            f"{name}: detected {true_ppi:.0f} PPI (grid {pitch:.1f} px/square), "
            f"already at or below {target_dpi} PPI; not upscaled"
        )
        return gray, target_dpi, note

    old = gray.size
    new_size = (max(1, round(gray.width * scale)), max(1, round(gray.height * scale)))
    resized = gray.resize(new_size, Image.Resampling.LANCZOS)
    note = (
        f"{name}: detected {true_ppi:.0f} PPI (grid {pitch:.1f} px/square) -> "
        f"{target_dpi} PPI, {old[0]}x{old[1]} -> {new_size[0]}x{new_size[1]}"
    )
    return resized, target_dpi, note


PRINT_WIDTH_INCHES = 8.5
PRINT_HEIGHT_INCHES = 11.0


def _resample_to_dpi(img: Image.Image, target_dpi: int) -> Image.Image:
    """Resize *img* to fit a standard page at *target_dpi*.

    Assumes the image represents a full page (8.5 x 11 inches) and scales
    so the longer side matches the corresponding page dimension at the
    target DPI.  This avoids relying on embedded DPI metadata.
    """
    if img.height >= img.width:
        # Portrait: longer side is 11 inches
        target_h = round(PRINT_HEIGHT_INCHES * target_dpi)
        scale = target_h / img.height
    else:
        # Landscape: longer side is 11 inches
        target_w = round(PRINT_HEIGHT_INCHES * target_dpi)
        scale = target_w / img.width

    if scale >= 1.0:
        return img

    new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


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

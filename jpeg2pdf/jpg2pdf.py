#!/usr/bin/env python3
"""
jpg2pdf - Combine sequentially-numbered JPEG files into PDFs, grouped by filename prefix.
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


# US Letter size in points
PAGE_WIDTH, PAGE_HEIGHT = LETTER  # 612 x 792 points


def parse_filename(filename: str) -> tuple[str, int] | None:
    """
    Parse a filename to extract prefix and sequence number.
    Returns (prefix, sequence_number) or None if doesn't match pattern.
    """
    match = re.match(r'^(.+)_(\d+)\.jpe?g$', filename, re.IGNORECASE)
    if match:
        prefix = match.group(1)
        sequence = int(match.group(2))
        return prefix, sequence
    return None


def scan_directory(directory: Path, prefix_filter: str | None = None) -> dict[str, list[tuple[int, Path]]]:
    """
    Scan directory for JPEG files matching the pattern.
    Returns dict mapping lowercase prefix to list of (sequence, filepath) tuples.
    """
    groups: dict[str, list[tuple[int, Path]]] = defaultdict(list)
    original_case: dict[str, str] = {}  # Track first-seen case for each prefix

    for entry in directory.iterdir():
        if not entry.is_file():
            continue

        parsed = parse_filename(entry.name)
        if parsed is None:
            print(f"Skipping: {entry.name} (doesn't match pattern)", file=sys.stderr)
            continue

        prefix, sequence = parsed
        prefix_lower = prefix.lower()

        # Apply prefix filter if specified
        if prefix_filter and prefix_lower != prefix_filter.lower():
            continue

        # Track original case from first file encountered
        if prefix_lower not in original_case:
            original_case[prefix_lower] = prefix

        groups[prefix_lower].append((sequence, entry))

    # Replace lowercase keys with original case
    result = {}
    for prefix_lower, files in groups.items():
        result[original_case[prefix_lower]] = files

    return result


def check_sequence_gaps(files: list[tuple[int, Path]], prefix: str) -> None:
    """Check for gaps in sequence numbers and warn if found."""
    sequences = sorted(seq for seq, _ in files)
    if not sequences:
        return

    expected = set(range(min(sequences), max(sequences) + 1))
    actual = set(sequences)
    missing = sorted(expected - actual)

    if missing:
        print(f'Warning: missing sequence number(s) {missing} in group "{prefix}"', file=sys.stderr)


def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """Apply EXIF orientation to image."""
    try:
        from PIL import ExifTags

        exif = img.getexif()
        if exif:
            orientation_tag = None
            for tag, name in ExifTags.TAGS.items():
                if name == 'Orientation':
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
        pass  # If EXIF processing fails, just use original orientation

    return img


def calculate_image_size(img_width: int, img_height: int) -> tuple[float, float, float, float]:
    """
    Calculate the size and position to fit image on US Letter page.
    Returns (x, y, width, height) in points.
    """
    # Page margins (0.5 inch on each side)
    margin = 0.5 * inch
    max_width = PAGE_WIDTH - 2 * margin
    max_height = PAGE_HEIGHT - 2 * margin

    # Calculate scale to fit within margins while preserving aspect ratio
    scale_w = max_width / img_width
    scale_h = max_height / img_height
    scale = min(scale_w, scale_h)

    new_width = img_width * scale
    new_height = img_height * scale

    # Center on page
    x = (PAGE_WIDTH - new_width) / 2
    y = (PAGE_HEIGHT - new_height) / 2

    return x, y, new_width, new_height


def create_pdf(files: list[tuple[int, Path]], output_path: Path, prefix: str) -> bool:
    """
    Create a PDF from a list of image files.
    Returns True on success, False if no valid images were processed.
    """
    # Sort by sequence number
    sorted_files = sorted(files, key=lambda x: x[0])

    c = canvas.Canvas(str(output_path), pagesize=LETTER)
    pages_added = 0

    for sequence, filepath in sorted_files:
        try:
            img = Image.open(filepath)
            img = apply_exif_orientation(img)

            # Convert to RGB if necessary (for CMYK or palette images)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Save to temporary file for reportlab
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, 'JPEG', quality=95)

            try:
                x, y, width, height = calculate_image_size(img.width, img.height)
                c.drawImage(tmp_path, x, y, width=width, height=height)
                c.showPage()
                pages_added += 1
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            print(f"Warning: Could not process {filepath.name}: {e}", file=sys.stderr)
            continue

    if pages_added > 0:
        c.save()
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        prog='jpg2pdf',
        description='Combine sequentially-numbered JPEG files into PDFs, grouped by filename prefix.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--prefix', '-p',
        help='Only process files matching this prefix (case-insensitive)'
    )
    parser.add_argument(
        '--output', '-o',
        default='./pdfs/',
        help='Output directory (default: ./pdfs/)'
    )

    args = parser.parse_args()

    # Validate input directory
    input_dir = Path(args.directory)
    if not input_dir.is_dir():
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Scan for files
    groups = scan_directory(input_dir, args.prefix)

    if not groups:
        print("Error: No valid files found", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each group
    success_count = 0
    for prefix, files in groups.items():
        check_sequence_gaps(files, prefix)

        output_path = output_dir / f"{prefix}.pdf"
        print(f"Creating {output_path} from {len(files)} image(s)...")

        if create_pdf(files, output_path, prefix):
            success_count += 1
        else:
            print(f"Error: No valid images in group '{prefix}'", file=sys.stderr)

    if success_count == 0:
        print("Error: No PDFs were created", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully created {success_count} PDF(s)")


if __name__ == '__main__':
    main()

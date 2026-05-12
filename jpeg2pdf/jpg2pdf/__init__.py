"""jpg2pdf - Combine sequentially-numbered JPEG files into PDFs."""

from .cli import main
from .core import (
    apply_exif_orientation,
    calculate_image_size,
    create_pdf,
    find_sequence_gaps,
    parse_filename,
    scan_directory,
)

__all__ = [
    "apply_exif_orientation",
    "calculate_image_size",
    "create_pdf",
    "find_sequence_gaps",
    "main",
    "parse_filename",
    "scan_directory",
]

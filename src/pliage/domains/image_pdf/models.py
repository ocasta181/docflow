"""Image-to-PDF domain models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImagePdfResult:
    """One PDF produced from a numbered image group."""

    prefix: str
    output_path: Path
    image_count: int

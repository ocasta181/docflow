"""OCR domain models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OcrResult:
    """Result of OCR processing for one PDF."""

    path: Path
    success: bool
    skipped: bool
    message: str


@dataclass(frozen=True)
class ExtractResult:
    """Result of text extraction for one PDF."""

    path: Path
    output_path: Path | None
    success: bool
    ocr_performed: bool
    message: str

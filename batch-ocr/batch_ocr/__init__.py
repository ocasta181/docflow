"""Batch OCR - Recursively OCR PDF files in directories."""

from .core import ocr_directory, ocr_pdf, find_pdfs, has_text, extract_text, OcrResult, ExtractResult
from .cli import main

__all__ = ["ocr_directory", "ocr_pdf", "find_pdfs", "has_text", "extract_text", "OcrResult", "ExtractResult", "main"]

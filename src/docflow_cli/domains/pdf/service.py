"""PDF page operation service."""

from pathlib import Path

from pypdf import PdfReader, PdfWriter

from docflow_cli.domains.pdf.models import SplitPart
from docflow_cli.shared import (
    atomic_output_path,
    ensure_file,
    ensure_output_not_inputs,
    require_extension,
)


PDF_EXTENSIONS = {".pdf"}


def page_count(input_path: Path | str) -> int:
    """Return the number of pages in a PDF."""
    pdf_path = _require_pdf_file(input_path)
    reader = PdfReader(pdf_path)
    return len(reader.pages)


def split_pdf(input_path: Path | str, num_parts: int = 2) -> list[SplitPart]:
    """Split a PDF into multiple sibling files."""
    pdf_path = _require_pdf_file(input_path)

    if num_parts < 2:
        raise ValueError("Number of parts must be at least 2")

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    if total_pages < num_parts:
        raise ValueError(f"PDF has only {total_pages} page(s), cannot split into {num_parts} parts")

    base_pages = total_pages // num_parts
    remainder = total_pages % num_parts

    parts: list[SplitPart] = []
    current_page = 0

    for part_index in range(num_parts):
        pages_in_part = base_pages + (1 if part_index < remainder else 0)
        start_page = current_page + 1
        end_page = current_page + pages_in_part
        output_path = pdf_path.with_name(f"{pdf_path.stem}_part{part_index + 1}{pdf_path.suffix}")

        writer = PdfWriter()
        for _ in range(pages_in_part):
            writer.add_page(reader.pages[current_page])
            current_page += 1

        _write_pdf(writer, output_path)
        parts.append(SplitPart(output_path, start_page, end_page))

    return parts


def reverse_pdf(input_path: Path | str, output_path: Path | str | None = None) -> Path:
    """Reverse the page order of a PDF."""
    pdf_path = _require_pdf_file(input_path)
    target_path = (
        Path(output_path)
        if output_path
        else pdf_path.with_name(f"{pdf_path.stem}_reversed{pdf_path.suffix}")
    )
    require_extension(target_path, PDF_EXTENSIONS, "Output")
    ensure_output_not_inputs(target_path, [pdf_path])

    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page_index in range(len(reader.pages) - 1, -1, -1):
        writer.add_page(reader.pages[page_index])

    return _write_pdf(writer, target_path)


def join_pdfs(output_path: Path | str, input_paths: list[Path] | tuple[Path, ...]) -> Path:
    """Join multiple PDFs into one output file."""
    if len(input_paths) < 2:
        raise ValueError("Need at least 2 PDF files to join")

    target_path = Path(output_path)
    require_extension(target_path, PDF_EXTENSIONS, "Output")
    pdf_paths = [_require_pdf_file(input_path) for input_path in input_paths]
    ensure_output_not_inputs(target_path, pdf_paths)

    writer = PdfWriter()
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    return _write_pdf(writer, target_path)


def _require_pdf_file(path: Path | str) -> Path:
    pdf_path = ensure_file(path)
    require_extension(pdf_path, PDF_EXTENSIONS, "Input")
    return pdf_path


def _write_pdf(writer: PdfWriter, output_path: Path) -> Path:
    with atomic_output_path(output_path) as temp_path:
        with temp_path.open("wb") as file:
            writer.write(file)
    return output_path

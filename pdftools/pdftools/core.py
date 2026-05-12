"""Core PDF manipulation functions."""

from pathlib import Path

from pypdf import PdfReader, PdfWriter


def split_pdf(input_path: Path, num_parts: int = 2) -> list[Path]:
    """
    Split a PDF into multiple parts.

    Args:
        input_path: Path to the input PDF file
        num_parts: Number of parts to split into (default: 2)

    Returns:
        List of paths to the output files.
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    if total_pages < num_parts:
        raise ValueError(
            f"PDF has only {total_pages} page(s), cannot split into {num_parts} parts"
        )

    if num_parts < 2:
        raise ValueError("Number of parts must be at least 2")

    # Calculate pages per part
    base_pages = total_pages // num_parts
    remainder = total_pages % num_parts

    # Create output paths
    stem = input_path.stem
    suffix = input_path.suffix
    parent = input_path.parent

    output_paths = []
    current_page = 0

    for part in range(num_parts):
        # Distribute remainder pages across first parts
        pages_in_part = base_pages + (1 if part < remainder else 0)

        output_path = parent / f"{stem}_part{part + 1}{suffix}"
        output_paths.append(output_path)

        writer = PdfWriter()
        for _ in range(pages_in_part):
            writer.add_page(reader.pages[current_page])
            current_page += 1

        with open(output_path, "wb") as f:
            writer.write(f)

    return output_paths


def reverse_pdf(input_path: Path, output_path: Path | None = None) -> Path:
    """
    Reverse the page order of a PDF.

    Args:
        input_path: Path to the input PDF file
        output_path: Optional explicit output path. If omitted, a sibling
            ``*_reversed.pdf`` file is created.

    Returns:
        Path to the output file.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_reversed{input_path.suffix}")

    if output_path.resolve() == input_path.resolve():
        raise ValueError("Output path must be different from input path")

    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page_index in range(len(reader.pages) - 1, -1, -1):
        writer.add_page(reader.pages[page_index])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def join_pdfs(output_path: Path, input_paths: list[Path]) -> Path:
    """
    Join multiple PDFs into one.

    Args:
        output_path: Path for the output PDF file
        input_paths: List of paths to input PDF files

    Returns:
        Path to the output file.
    """
    if len(input_paths) < 2:
        raise ValueError("Need at least 2 PDF files to join")

    writer = PdfWriter()

    for input_path in input_paths:
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")
        reader = PdfReader(input_path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path

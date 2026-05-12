"""Command-line interface for jpg2pdf."""

import argparse
import sys
from pathlib import Path

from .core import create_pdf, find_sequence_gaps, scan_directory


def _warn(message: str) -> None:
    print(message, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="jpg2pdf",
        description="Combine sequentially-numbered JPEG files into PDFs, grouped by filename prefix.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--prefix",
        "-p",
        help="Only process files matching this prefix (case-insensitive)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="./pdfs/",
        help="Output directory (default: ./pdfs/)",
    )

    args = parser.parse_args(argv)

    input_dir = Path(args.directory)
    if not input_dir.is_dir():
        print(f"Error: {args.directory} is not a directory", file=sys.stderr)
        return 1

    groups = scan_directory(input_dir, args.prefix, warn=_warn)

    if not groups:
        print("Error: No valid files found", file=sys.stderr)
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    for prefix, files in groups.items():
        missing = find_sequence_gaps(files)
        if missing:
            print(
                f'Warning: missing sequence number(s) {missing} in group "{prefix}"',
                file=sys.stderr,
            )

        output_path = output_dir / f"{prefix}.pdf"
        print(f"Creating {output_path} from {len(files)} image(s)...")

        if create_pdf(files, output_path, warn=_warn):
            success_count += 1
        else:
            print(f"Error: No valid images in group '{prefix}'", file=sys.stderr)

    if success_count == 0:
        print("Error: No PDFs were created", file=sys.stderr)
        return 1

    print(f"Successfully created {success_count} PDF(s)")
    return 0

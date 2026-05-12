"""CLI router for image-to-PDF workflows."""

import argparse
import sys
from pathlib import Path

from docflow.shared import PathValidationError


def register_image_parser(subparsers: argparse._SubParsersAction) -> None:
    image_parser = subparsers.add_parser("image", help="Image document workflows")
    image_subparsers = image_parser.add_subparsers(dest="image_command", required=True)

    to_pdf_parser = image_subparsers.add_parser(
        "to-pdf",
        help="Combine sequentially-numbered JPEG files into PDFs",
    )
    to_pdf_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    to_pdf_parser.add_argument(
        "--prefix",
        "-p",
        help="Only process files matching this prefix (case-insensitive)",
    )
    to_pdf_parser.add_argument(
        "--output",
        "-o",
        default="./pdfs/",
        help="Output directory (default: ./pdfs/)",
    )
    to_pdf_parser.set_defaults(handler=cmd_to_pdf)


def cmd_to_pdf(args: argparse.Namespace) -> int:
    from .service import create_pdfs_from_directory

    try:
        results, warnings = create_pdfs_from_directory(
            Path(args.directory),
            Path(args.output),
            prefix_filter=args.prefix,
        )
    except (PathValidationError, OSError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(warning, file=sys.stderr)

    for result in results:
        print(f"Created: {result.output_path} from {result.image_count} image(s)")

    print(f"Successfully created {len(results)} PDF(s)")
    return 0

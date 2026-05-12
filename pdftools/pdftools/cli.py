"""Command-line interface for pdftools."""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader

from .core import split_pdf, join_pdfs, reverse_pdf


def cmd_split(args: argparse.Namespace) -> int:
    """Handle split subcommand."""
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        print(f"Input: {input_path}")
        print(f"Total pages: {total_pages}")
        print(f"Splitting into {args.parts} parts")
        print()

        output_paths = split_pdf(input_path, args.parts)

        # Calculate page ranges for display
        pages_per_part = total_pages // args.parts
        remainder = total_pages % args.parts
        current_page = 1

        for i, path in enumerate(output_paths):
            pages_in_part = pages_per_part + (1 if i < remainder else 0)
            end_page = current_page + pages_in_part - 1
            print(f"Created: {path} (pages {current_page}-{end_page})")
            current_page = end_page + 1

        print()
        print("Original file unchanged.")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_join(args: argparse.Namespace) -> int:
    """Handle join subcommand."""
    output_path = Path(args.output)
    input_paths = [Path(p) for p in args.inputs]

    # Check all input files exist
    for path in input_paths:
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            return 1

    try:
        total_pages = 0
        print("Joining PDF files:")
        for path in input_paths:
            reader = PdfReader(path)
            pages = len(reader.pages)
            total_pages += pages
            print(f"  {path} ({pages} pages)")

        print()

        join_pdfs(output_path, input_paths)

        print(f"Created: {output_path} ({total_pages} pages)")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_reverse(args: argparse.Namespace) -> int:
    """Handle reverse subcommand."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)

        print(f"Input: {input_path}")
        print(f"Total pages: {total_pages}")
        print("Reversing page order")
        print()

        created_path = reverse_pdf(input_path, output_path)

        print(f"Created: {created_path} ({total_pages} pages)")
        print()
        print("Original file unchanged.")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Split, join, and reverse PDF files (non-destructive)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Split subcommand
    split_parser = subparsers.add_parser("split", help="Split a PDF into multiple parts")
    split_parser.add_argument("input", help="Input PDF file")
    split_parser.add_argument(
        "--parts",
        "-n",
        type=int,
        default=2,
        help="Number of parts to split into (default: 2)",
    )

    # Join subcommand
    join_parser = subparsers.add_parser("join", help="Join multiple PDFs into one")
    join_parser.add_argument("output", help="Output PDF file")
    join_parser.add_argument("inputs", nargs="+", help="Input PDF files to join")

    # Reverse subcommand
    reverse_parser = subparsers.add_parser(
        "reverse", help="Reverse the page order of a PDF"
    )
    reverse_parser.add_argument("input", help="Input PDF file")
    reverse_parser.add_argument(
        "--output",
        "-o",
        help="Output PDF file (default: INPUTNAME_reversed.pdf)",
    )

    args = parser.parse_args()

    if args.command == "split":
        return cmd_split(args)
    elif args.command == "join":
        return cmd_join(args)
    elif args.command == "reverse":
        return cmd_reverse(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

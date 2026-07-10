"""CLI router for PDF operations."""

import argparse
import sys
from pathlib import Path

from pliage.cli.output import add_json_argument, emit_json
from pliage.shared import PathValidationError


def register_pdf_parser(subparsers: argparse._SubParsersAction) -> None:
    pdf_parser = subparsers.add_parser("pdf", help="PDF page operations")
    pdf_subparsers = pdf_parser.add_subparsers(dest="pdf_command", required=True)

    reverse_parser = pdf_subparsers.add_parser(
        "reverse",
        help="Reverse the page order of a PDF",
    )
    reverse_parser.add_argument("input", help="Input PDF file")
    reverse_parser.add_argument(
        "--output",
        "-o",
        help="Output PDF file (default: INPUTNAME_reversed.pdf)",
    )
    add_json_argument(reverse_parser)
    reverse_parser.set_defaults(handler=cmd_reverse)

    join_parser = pdf_subparsers.add_parser("join", help="Join multiple PDFs into one")
    join_parser.add_argument("output", help="Output PDF file")
    join_parser.add_argument("inputs", nargs="+", help="Input PDF files to join")
    add_json_argument(join_parser)
    join_parser.set_defaults(handler=cmd_join)

    split_parser = pdf_subparsers.add_parser("split", help="Split a PDF into multiple parts")
    split_parser.add_argument("input", help="Input PDF file")
    split_parser.add_argument(
        "--parts",
        "-n",
        type=int,
        default=2,
        help="Number of parts to split into (default: 2)",
    )
    add_json_argument(split_parser)
    split_parser.set_defaults(handler=cmd_split)


def cmd_reverse(args: argparse.Namespace) -> int:
    from .service import page_count, reverse_pdf

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    try:
        total_pages = page_count(input_path)
        created_path = reverse_pdf(input_path, output_path)
    except (PathValidationError, OSError, ValueError) as e:
        if args.json:
            emit_json({"success": False, "error": str(e)})
            return 1
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        emit_json(
            {
                "success": True,
                "command": "pdf reverse",
                "input": input_path,
                "output": created_path,
                "pages": total_pages,
            }
        )
        return 0

    print(f"Input: {input_path}")
    print(f"Total pages: {total_pages}")
    print("Reversing page order")
    print()
    print(f"Created: {created_path} ({total_pages} pages)")
    print()
    print("Original file unchanged.")
    return 0


def cmd_join(args: argparse.Namespace) -> int:
    from .service import join_pdfs, page_count

    output_path = Path(args.output)
    input_paths = [Path(path) for path in args.inputs]

    try:
        counts = [(path, page_count(path)) for path in input_paths]
        created_path = join_pdfs(output_path, input_paths)
    except (PathValidationError, OSError, ValueError) as e:
        if args.json:
            emit_json({"success": False, "error": str(e)})
            return 1
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        emit_json(
            {
                "success": True,
                "command": "pdf join",
                "output": created_path,
                "inputs": [{"path": path, "pages": count} for path, count in counts],
                "pages": sum(count for _, count in counts),
            }
        )
        return 0

    print("Joining PDF files:")
    for path, count in counts:
        print(f"  {path} ({count} pages)")
    print()
    print(f"Created: {created_path} ({sum(count for _, count in counts)} pages)")
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    from .service import page_count, split_pdf

    input_path = Path(args.input)

    try:
        total_pages = page_count(input_path)
        parts = split_pdf(input_path, args.parts)
    except (PathValidationError, OSError, ValueError) as e:
        if args.json:
            emit_json({"success": False, "error": str(e)})
            return 1
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        emit_json(
            {
                "success": True,
                "command": "pdf split",
                "input": input_path,
                "pages": total_pages,
                "parts": parts,
            }
        )
        return 0

    print(f"Input: {input_path}")
    print(f"Total pages: {total_pages}")
    print(f"Splitting into {args.parts} parts")
    print()
    for part in parts:
        print(f"Created: {part.path} (pages {part.start_page}-{part.end_page})")
    print()
    print("Original file unchanged.")
    return 0

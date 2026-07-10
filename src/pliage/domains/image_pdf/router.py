"""CLI router for image-to-PDF workflows."""

import argparse
import sys
from pathlib import Path

from pliage.cli.output import add_json_argument, emit_json
from pliage.shared import PathValidationError


def register_image_parser(subparsers: argparse._SubParsersAction) -> None:
    image_parser = subparsers.add_parser("image", help="Image document workflows")
    image_subparsers = image_parser.add_subparsers(dest="image_command", required=True)

    to_pdf_parser = image_subparsers.add_parser(
        "to-pdf",
        help="Combine sequentially-numbered JPEG or PNG files into PDFs",
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
    add_json_argument(to_pdf_parser)
    to_pdf_parser.set_defaults(handler=cmd_to_pdf)

    to_bw_parser = image_subparsers.add_parser(
        "to-bw",
        help="Convert images to black-and-white (grayscale) PNGs",
    )
    to_bw_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing images (default: current directory)",
    )
    to_bw_parser.add_argument(
        "--output",
        "-o",
        help="Output directory (default: overwrite in place as PNG)",
    )
    to_bw_parser.add_argument(
        "--dpi",
        type=int,
        help="Target output resolution in DPI/PPI (e.g. 150)",
    )
    to_bw_parser.add_argument(
        "--detect-size",
        action="store_true",
        help="Measure true resolution from a reference grid instead of assuming page size",
    )
    to_bw_parser.add_argument(
        "--grid",
        nargs="?",
        const="1cm",
        default=None,
        metavar="SIZE",
        help="Grid-square size for --detect-size (e.g. 1cm, 5mm, 0.5in; default 1cm)",
    )
    add_json_argument(to_bw_parser)
    to_bw_parser.set_defaults(handler=cmd_to_bw)


def cmd_to_bw(args: argparse.Namespace) -> int:
    from .service import convert_to_grayscale, parse_grid_size_cm

    detect_size = args.detect_size or args.grid is not None
    try:
        if detect_size and args.dpi is None:
            raise ValueError("--detect-size requires a target --dpi (e.g. --dpi 150)")
        grid_size_cm = parse_grid_size_cm(args.grid or "1cm") if detect_size else None
        converted, warnings = convert_to_grayscale(
            Path(args.directory),
            output_dir=Path(args.output) if args.output else None,
            dpi=args.dpi,
            detect_size=detect_size,
            grid_size_cm=grid_size_cm,
        )
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
                "command": "image to-bw",
                "converted": [str(p) for p in converted],
                "warnings": warnings,
            }
        )
        return 0

    for warning in warnings:
        print(warning, file=sys.stderr)

    for path in converted:
        print(f"Converted: {path}")

    print(f"Successfully converted {len(converted)} image(s) to grayscale")
    return 0


def cmd_to_pdf(args: argparse.Namespace) -> int:
    from .service import create_pdfs_from_directory

    try:
        results, warnings = create_pdfs_from_directory(
            Path(args.directory),
            Path(args.output),
            prefix_filter=args.prefix,
        )
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
                "command": "image to-pdf",
                "results": results,
                "warnings": warnings,
            }
        )
        return 0

    for warning in warnings:
        print(warning, file=sys.stderr)

    for result in results:
        print(f"Created: {result.output_path} from {result.image_count} image(s)")

    print(f"Successfully created {len(results)} PDF(s)")
    return 0

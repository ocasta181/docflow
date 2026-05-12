"""Top-level docflow command-line interface."""

import argparse
import sys

from docflow.cli.errors import format_optional_dependency_error
from docflow.domains.image_pdf.router import register_image_parser
from docflow.domains.ocr.router import register_ocr_parser
from docflow.domains.pdf.router import register_pdf_parser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docflow",
        description="Document workflow utilities",
    )
    subparsers = parser.add_subparsers(dest="domain", required=True)
    register_image_parser(subparsers)
    register_ocr_parser(subparsers)
    register_pdf_parser(subparsers)

    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except ModuleNotFoundError as error:
        message = format_optional_dependency_error(error)
        if message is None:
            raise
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

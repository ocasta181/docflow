"""Top-level docflow command-line interface."""

import argparse
import sys

from docflow.domains.pdf.router import register_pdf_parser


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="docflow",
        description="Document workflow utilities",
    )
    subparsers = parser.add_subparsers(dest="domain", required=True)
    register_pdf_parser(subparsers)

    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())

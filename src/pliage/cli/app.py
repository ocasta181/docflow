"""Top-level pliage command-line interface."""

import argparse
from importlib.metadata import PackageNotFoundError, version
import sys

from pliage.cli.errors import format_optional_dependency_error, get_optional_dependency
from pliage.cli.output import emit_json
from pliage.domains.image_pdf.router import register_image_parser
from pliage.domains.ocr.router import register_ocr_parser
from pliage.domains.pdf.router import register_pdf_parser


def main(argv: list[str] | None = None) -> int:
    cli_args = list(sys.argv[1:] if argv is None else argv)
    if cli_args == ["--version"]:
        print(f"pliage {_package_version()}")
        return 0

    parser = argparse.ArgumentParser(
        prog="pliage",
        description="Document workflow utilities",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the installed version and exit",
    )
    subparsers = parser.add_subparsers(dest="domain", required=True)
    register_image_parser(subparsers)
    register_ocr_parser(subparsers)
    register_pdf_parser(subparsers)

    try:
        args = parser.parse_args(cli_args)
    except SystemExit as error:
        return error.code if isinstance(error.code, int) else 1
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except ModuleNotFoundError as error:
        dependency = get_optional_dependency(error)
        if dependency is None:
            raise
        message = format_optional_dependency_error(error)
        if getattr(args, "json", False):
            emit_json(
                {
                    "success": False,
                    "error": message,
                    "missing_dependency": {
                        "package": dependency.package_name,
                        "extra": dependency.extra,
                    },
                }
            )
            return 1
        print(message, file=sys.stderr)
        return 1


def _package_version() -> str:
    try:
        return version("pliage")
    except PackageNotFoundError:
        return "0+unknown"


if __name__ == "__main__":
    sys.exit(main())

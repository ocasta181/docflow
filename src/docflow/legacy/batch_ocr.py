"""Compatibility wrapper for the legacy batch-ocr command."""

import argparse
import sys

from docflow.cli.app import main as docflow_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if _has_help_flag(args):
        _create_parser().print_help()
        return 0

    command = "extract" if _remove_extract_flag(args) else "run"
    if command == "extract":
        _remove_force_flag(args)
    return docflow_main(["ocr", command, *args])


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recursively OCR PDF files in directories")
    parser.add_argument("path", help="Directory to process (or single PDF file)")
    parser.add_argument(
        "--no-recursive",
        "-n",
        action="store_true",
        help="Don't process subdirectories",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Run OCR even on files that already have text",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be processed without running OCR",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors and summary",
    )
    parser.add_argument(
        "--extract",
        "-e",
        action="store_true",
        help="Extract text to .txt files (runs OCR first if needed)",
    )
    return parser


def _has_help_flag(args: list[str]) -> bool:
    return "-h" in args or "--help" in args


def _remove_extract_flag(args: list[str]) -> bool:
    extract = False
    remaining = []

    for arg in args:
        if arg == "--extract":
            extract = True
            continue
        if arg == "-e":
            extract = True
            continue
        remaining.append(arg)

    args[:] = remaining
    return extract


def _remove_force_flag(args: list[str]) -> None:
    args[:] = [arg for arg in args if arg not in {"--force", "-f"}]

"""Compatibility wrapper for the legacy pdftools command."""

import sys

from docflow.cli.app import main as docflow_main


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return docflow_main(["pdf", *args])

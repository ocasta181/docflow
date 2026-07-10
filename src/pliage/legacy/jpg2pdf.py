"""Compatibility wrapper for the legacy jpg2pdf command."""

import sys

from pliage.cli.app import main as pliage_main


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return pliage_main(["image", "to-pdf", *args])

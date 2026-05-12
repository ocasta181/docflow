"""Tesseract runtime helpers."""

from pathlib import Path
import os
import sys


def get_tesseract_cmd() -> str:
    """Return the executable path for Tesseract."""
    bundle_dir = _get_bundle_dir()
    if bundle_dir:
        return str(bundle_dir / "tesseract")
    return "tesseract"


def get_tesseract_env() -> dict[str, str]:
    """Return environment variables for Tesseract subprocesses."""
    env = os.environ.copy()
    bundle_dir = _get_bundle_dir()
    if bundle_dir:
        env["TESSDATA_PREFIX"] = str(bundle_dir / "tessdata")
    return env


def _get_bundle_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return None

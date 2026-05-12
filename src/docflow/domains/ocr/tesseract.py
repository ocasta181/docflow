"""Tesseract runtime helpers."""

from pathlib import Path
import os
import shutil
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


def tesseract_unavailable_message() -> str | None:
    cmd = get_tesseract_cmd()
    if _is_path_command(cmd):
        if Path(cmd).exists():
            return None
        return f"Tesseract executable not found: {cmd}"

    if shutil.which(cmd) is not None:
        return None

    return (
        "Tesseract executable not found. Install Tesseract and ensure it is on PATH, "
        "or use a standalone build that bundles Tesseract."
    )


def _get_bundle_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return None


def _is_path_command(command: str) -> bool:
    return os.sep in command or (os.altsep is not None and os.altsep in command)

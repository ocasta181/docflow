"""PDF domain models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SplitPart:
    """One output file produced by splitting a PDF."""

    path: Path
    start_page: int
    end_page: int

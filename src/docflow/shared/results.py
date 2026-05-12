"""Shared command result models."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    """Outcome returned by command services before CLI formatting."""

    success: bool
    message: str
    output_paths: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def exit_code(self) -> int:
        return 0 if self.success else 1

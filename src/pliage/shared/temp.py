"""Temporary-output helpers."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import tempfile


@contextmanager
def atomic_output_path(output_path: Path | str) -> Iterator[Path]:
    """
    Yield a temporary sibling path and replace the target after successful work.

    The temporary file is created in the output directory so the final replace
    stays on the same filesystem.
    """
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    handle = tempfile.NamedTemporaryFile(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    handle.close()

    try:
        yield temp_path
        temp_path.replace(target)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

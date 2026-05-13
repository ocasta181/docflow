from pathlib import Path

import pytest

from pliage.shared import atomic_output_path


def test_atomic_output_path_replaces_target_on_success(tmp_path: Path) -> None:
    output_path = tmp_path / "output.txt"

    with atomic_output_path(output_path) as temp_path:
        temp_path.write_text("new content")
        assert temp_path.parent == output_path.parent
        assert temp_path != output_path

    assert output_path.read_text() == "new content"
    assert not temp_path.exists()


def test_atomic_output_path_preserves_target_on_failure(tmp_path: Path) -> None:
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with pytest.raises(RuntimeError, match="stop"):
        with atomic_output_path(output_path) as temp_path:
            temp_path.write_text("new content")
            raise RuntimeError("stop")

    assert output_path.read_text() == "old content"
    assert not temp_path.exists()

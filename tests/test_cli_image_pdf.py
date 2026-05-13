import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from pliage.cli.app import main


def create_test_jpeg(path: Path) -> None:
    image = Image.new("RGB", (200, 300), (0, 120, 255))
    image.save(path, "JPEG")


def test_pliage_image_to_pdf_command(tmp_path: Path, capsys) -> None:
    create_test_jpeg(tmp_path / "scan_1.jpg")
    create_test_jpeg(tmp_path / "scan_2.jpg")
    output_dir = tmp_path / "pdfs"

    result = main(["image", "to-pdf", str(tmp_path), "--output", str(output_dir)])

    assert result == 0
    assert len(PdfReader(output_dir / "scan.pdf").pages) == 2
    captured = capsys.readouterr()
    assert "Successfully created 1 PDF" in captured.out


def test_pliage_image_to_pdf_json_output(tmp_path: Path, capsys) -> None:
    create_test_jpeg(tmp_path / "scan_1.jpg")
    output_dir = tmp_path / "pdfs"

    result = main(["image", "to-pdf", str(tmp_path), "--output", str(output_dir), "--json"])

    assert result == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "command": "image to-pdf",
        "results": [
            {
                "image_count": 1,
                "output_path": str(output_dir / "scan.pdf"),
                "prefix": "scan",
            }
        ],
        "success": True,
        "warnings": [],
    }


def test_pliage_image_to_pdf_reports_errors(tmp_path: Path, capsys) -> None:
    result = main(["image", "to-pdf", str(tmp_path / "missing")])

    assert result == 1
    captured = capsys.readouterr()
    assert "Directory not found" in captured.err

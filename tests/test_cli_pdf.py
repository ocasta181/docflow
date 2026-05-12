import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from docflow.cli.app import main


def create_test_pdf(path: Path, page_count: int) -> Path:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as file:
        writer.write(file)
    return path


def test_docflow_pdf_reverse_command(tmp_path: Path, capsys) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", 2)

    result = main(["pdf", "reverse", str(input_pdf)])

    assert result == 0
    assert (tmp_path / "input_reversed.pdf").exists()
    captured = capsys.readouterr()
    assert "Created:" in captured.out


def test_docflow_pdf_reverse_json_output(tmp_path: Path, capsys) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", 2)

    result = main(["pdf", "reverse", str(input_pdf), "--json"])

    assert result == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {
        "command": "pdf reverse",
        "input": str(input_pdf),
        "output": str(tmp_path / "input_reversed.pdf"),
        "pages": 2,
        "success": True,
    }


def test_docflow_pdf_join_command(tmp_path: Path, capsys) -> None:
    first = create_test_pdf(tmp_path / "first.pdf", 1)
    second = create_test_pdf(tmp_path / "second.pdf", 2)
    output = tmp_path / "joined.pdf"

    result = main(["pdf", "join", str(output), str(first), str(second)])

    assert result == 0
    assert len(PdfReader(output).pages) == 3
    captured = capsys.readouterr()
    assert "Joining PDF files:" in captured.out


def test_docflow_pdf_split_command(tmp_path: Path, capsys) -> None:
    input_pdf = create_test_pdf(tmp_path / "input.pdf", 4)

    result = main(["pdf", "split", str(input_pdf), "--parts", "2"])

    assert result == 0
    assert (tmp_path / "input_part1.pdf").exists()
    assert (tmp_path / "input_part2.pdf").exists()
    captured = capsys.readouterr()
    assert "Splitting into 2 parts" in captured.out


def test_docflow_pdf_command_reports_errors(tmp_path: Path, capsys) -> None:
    result = main(["pdf", "reverse", str(tmp_path / "missing.pdf")])

    assert result == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_docflow_pdf_json_reports_errors(tmp_path: Path, capsys) -> None:
    result = main(["pdf", "reverse", str(tmp_path / "missing.pdf"), "--json"])

    assert result == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["success"] is False
    assert "File not found" in payload["error"]
    assert captured.err == ""

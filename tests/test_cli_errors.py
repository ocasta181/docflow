import json

import pytest

from pliage.cli.app import main
import pliage.domains.image_pdf.router as image_router
import pliage.domains.ocr.router as ocr_router
import pliage.domains.pdf.router as pdf_router


@pytest.mark.parametrize(
    ("router", "handler_name", "argv", "import_name", "package_name", "extra"),
    [
        (
            pdf_router,
            "cmd_reverse",
            ["pdf", "reverse", "input.pdf"],
            "pypdf",
            "pypdf",
            "pdf",
        ),
        (
            image_router,
            "cmd_to_pdf",
            ["image", "to-pdf", "."],
            "PIL",
            "Pillow",
            "image",
        ),
        (
            ocr_router,
            "cmd_run",
            ["ocr", "run", "input.pdf"],
            "fitz",
            "PyMuPDF",
            "ocr",
        ),
    ],
)
def test_missing_optional_dependency_prints_install_hint(
    monkeypatch,
    capsys,
    router,
    handler_name: str,
    argv: list[str],
    import_name: str,
    package_name: str,
    extra: str,
) -> None:
    def missing_dependency(_args) -> int:
        raise ModuleNotFoundError(f"No module named '{import_name}'", name=import_name)

    monkeypatch.setattr(router, handler_name, missing_dependency)

    result = main(argv)

    assert result == 1
    captured = capsys.readouterr()
    assert f"Missing optional dependency: {package_name}" in captured.err
    assert f"pliage[{extra}]" in captured.err
    assert "pliage[all]" in captured.err


def test_missing_optional_dependency_respects_json(monkeypatch, capsys) -> None:
    def missing_dependency(_args) -> int:
        raise ModuleNotFoundError("No module named 'pypdf'", name="pypdf")

    monkeypatch.setattr(pdf_router, "cmd_reverse", missing_dependency)

    result = main(["pdf", "reverse", "input.pdf", "--json"])

    assert result == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "error": "Missing optional dependency: pypdf. Install with `pliage[pdf]` or `pliage[all]`.",
        "missing_dependency": {"extra": "pdf", "package": "pypdf"},
        "success": False,
    }


def test_unknown_module_not_found_errors_are_not_swallowed(monkeypatch) -> None:
    def missing_internal_module(_args) -> int:
        raise ModuleNotFoundError("No module named 'internal_module'", name="internal_module")

    monkeypatch.setattr(pdf_router, "cmd_reverse", missing_internal_module)

    with pytest.raises(ModuleNotFoundError, match="internal_module"):
        main(["pdf", "reverse", "input.pdf"])

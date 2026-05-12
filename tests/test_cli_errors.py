import pytest

from docflow.cli.app import main
import docflow.domains.pdf.router as pdf_router


def test_missing_optional_dependency_prints_install_hint(monkeypatch, capsys) -> None:
    def missing_dependency(_args) -> int:
        raise ModuleNotFoundError("No module named 'pypdf'", name="pypdf")

    monkeypatch.setattr(pdf_router, "cmd_reverse", missing_dependency)

    result = main(["pdf", "reverse", "input.pdf"])

    assert result == 1
    captured = capsys.readouterr()
    assert "Missing optional dependency: pypdf" in captured.err
    assert "docflow[pdf]" in captured.err
    assert "docflow[all]" in captured.err


def test_unknown_module_not_found_errors_are_not_swallowed(monkeypatch) -> None:
    def missing_internal_module(_args) -> int:
        raise ModuleNotFoundError("No module named 'internal_module'", name="internal_module")

    monkeypatch.setattr(pdf_router, "cmd_reverse", missing_internal_module)

    with pytest.raises(ModuleNotFoundError, match="internal_module"):
        main(["pdf", "reverse", "input.pdf"])

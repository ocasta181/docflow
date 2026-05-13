from importlib.metadata import version

from docflow_cli.cli.app import main


def test_docflow_version_prints_package_version(capsys) -> None:
    result = main(["--version"])

    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == f"docflow {version('docflow-cli')}\n"
    assert captured.err == ""


def test_docflow_help_lists_version_option(capsys) -> None:
    result = main(["--help"])

    assert result == 0
    captured = capsys.readouterr()
    assert "--version" in captured.out

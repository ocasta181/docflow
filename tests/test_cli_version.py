from importlib.metadata import version

from pliage.cli.app import main


def test_pliage_version_prints_package_version(capsys) -> None:
    result = main(["--version"])

    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == f"pliage {version('pliage')}\n"
    assert captured.err == ""


def test_pliage_help_lists_version_option(capsys) -> None:
    result = main(["--help"])

    assert result == 0
    captured = capsys.readouterr()
    assert "--version" in captured.out

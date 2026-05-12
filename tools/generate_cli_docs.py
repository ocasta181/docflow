"""Generate CLI reference docs from argparse help output."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from docflow.cli.app import main


COMMANDS = [
    ("docflow", []),
    ("docflow pdf", ["pdf"]),
    ("docflow pdf reverse", ["pdf", "reverse"]),
    ("docflow pdf join", ["pdf", "join"]),
    ("docflow pdf split", ["pdf", "split"]),
    ("docflow image", ["image"]),
    ("docflow image to-pdf", ["image", "to-pdf"]),
    ("docflow ocr", ["ocr"]),
    ("docflow ocr run", ["ocr", "run"]),
    ("docflow ocr extract", ["ocr", "extract"]),
]


def render_help(args: list[str]) -> str:
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        exit_code = main([*args, "--help"])
    if exit_code != 0:
        raise RuntimeError(f"Help command failed for: {args}")
    return output.getvalue().strip()


def main_cli() -> int:
    sections = [
        "# CLI Reference",
        "",
        "Generated from the current `docflow` command help.",
        "",
    ]

    for title, args in COMMANDS:
        sections.extend(
            [
                f"## `{title}`",
                "",
                "```text",
                render_help(args),
                "```",
                "",
            ]
        )

    Path("docs/cli.md").write_text("\n".join(sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

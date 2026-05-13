"""Generate CLI reference docs from argparse help output."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from pliage.cli.app import main


COMMANDS = [
    ("pliage", []),
    ("pliage pdf", ["pdf"]),
    ("pliage pdf reverse", ["pdf", "reverse"]),
    ("pliage pdf join", ["pdf", "join"]),
    ("pliage pdf split", ["pdf", "split"]),
    ("pliage image", ["image"]),
    ("pliage image to-pdf", ["image", "to-pdf"]),
    ("pliage ocr", ["ocr"]),
    ("pliage ocr run", ["ocr", "run"]),
    ("pliage ocr extract", ["ocr", "extract"]),
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
        "Generated from the current `pliage` command help.",
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

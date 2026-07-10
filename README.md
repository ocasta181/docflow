# pliage

Small command-line utilities for document workflows.

`pliage` is both the distribution package name and the primary executable.

See [docs/publishing.md](docs/publishing.md) for release and publishing steps.
See [docs/json-output.md](docs/json-output.md) for machine-readable output
contracts.
See [docs/why-pliage-exists.md](docs/why-pliage-exists.md) for the project
rationale and comparable public tools.

## Requirements

- Python 3.10 or newer
- Tesseract on `PATH` for OCR commands
- The `all` extra for the complete toolset

Feature extras are split by domain:

- `pdf`: PDF page operations
- `image`: JPEG/PNG-to-PDF conversion
- `ocr`: OCR and text extraction
- `all`: every runtime feature
- `dev`: local testing, linting, formatting, and release tooling

## Install

From a source checkout:

```bash
uv sync --extra all --extra dev
uv run pliage --help
```

After package publication:

```bash
uv tool install "pliage[all]"
pliage --help
```

## Commands

Use `pliage pdf` for PDF page operations:

```bash
uv run pliage pdf reverse input.pdf
uv run pliage pdf join combined.pdf first.pdf second.pdf
uv run pliage pdf split input.pdf --parts 3
```

Use `pliage image to-pdf` to combine sequentially numbered JPEG or PNG
files into PDFs grouped by filename prefix:

```bash
uv run pliage image to-pdf ./scans --output ./pdfs
uv run pliage image to-pdf ./scans --prefix invoice
```

Use `pliage ocr` for OCR and text extraction:

```bash
uv run pliage ocr run ./pdfs
uv run pliage ocr run ./pdfs --output-dir ./ocr-pdfs
uv run pliage ocr run ./document.pdf --output ./document_ocr.pdf
uv run pliage ocr run ./document.pdf --lang eng+spa
uv run pliage ocr extract ./pdfs
uv run pliage ocr run ./document.pdf --force
```

Add `--json` to a command when a script needs stable machine-readable output
instead of human progress text:

```bash
uv run pliage pdf reverse input.pdf --json
uv run pliage ocr run ./pdfs --output-dir ./ocr-pdfs --json
```

## OCR Runtime

OCR uses PyMuPDF for PDF inspection/manipulation and shells out to the
`tesseract` executable to create page-level OCR output. In normal Python
installs, `tesseract` must be installed separately and available on `PATH`.
If OCR is needed and Tesseract cannot be found, `pliage` fails before page
processing starts and prints installation guidance.

When running from a frozen standalone binary, the runtime first looks for a
bundled `tesseract` executable and `tessdata` directory beside the extracted
application bundle. If those are not bundled, the standalone build must document
that it still expects system Tesseract.

`just build` currently builds the Python source distribution and wheel. Any
standalone executable build should be treated as a release artifact generated
from a clean checkout, not as checked-in source.

## Development

```bash
just setup
just lint
just test-all
just check
just build
```

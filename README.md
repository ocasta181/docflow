# docflow

Small command-line utilities for document workflows.

`docflow` is the package name and primary executable. The legacy command names
`pdftools`, `jpg2pdf`, and `batch-ocr` are still available as compatibility
aliases while the project finishes migration.

See [docs/publishing.md](docs/publishing.md) for release and publishing steps.

## Requirements

- Python 3.10 or newer
- Tesseract on `PATH` for OCR commands
- The `all` extra for the complete toolset

Feature extras are split by domain:

- `pdf`: PDF page operations
- `image`: JPEG-to-PDF conversion
- `ocr`: OCR and text extraction
- `all`: every runtime feature
- `dev`: local testing, linting, formatting, and release tooling

## Install

From a source checkout:

```bash
uv sync --extra all --extra dev
uv run docflow --help
```

After package publication:

```bash
uv tool install "docflow[all]"
docflow --help
```

## Commands

Use `docflow pdf` for PDF page operations:

```bash
uv run docflow pdf reverse input.pdf
uv run docflow pdf join combined.pdf first.pdf second.pdf
uv run docflow pdf split input.pdf --parts 3
```

Use `docflow image to-pdf` to combine sequentially numbered JPEG files into
PDFs grouped by filename prefix:

```bash
uv run docflow image to-pdf ./scans --output ./pdfs
uv run docflow image to-pdf ./scans --prefix invoice
```

Use `docflow ocr` for OCR and text extraction:

```bash
uv run docflow ocr run ./pdfs
uv run docflow ocr run ./pdfs --output-dir ./ocr-pdfs
uv run docflow ocr run ./document.pdf --output ./document_ocr.pdf
uv run docflow ocr run ./document.pdf --lang eng+spa
uv run docflow ocr extract ./pdfs
uv run docflow ocr run ./document.pdf --force
```

Add `--json` to a command when a script needs stable machine-readable output
instead of human progress text:

```bash
uv run docflow pdf reverse input.pdf --json
uv run docflow ocr run ./pdfs --output-dir ./ocr-pdfs --json
```

## Legacy Aliases

The original executable names route to the unified command:

```bash
uv run pdftools reverse input.pdf
uv run jpg2pdf ./scans --output ./pdfs
uv run batch-ocr ./pdfs --extract
```

New scripts should prefer `docflow`.

## OCR Runtime

OCR uses PyMuPDF for PDF inspection/manipulation and shells out to the
`tesseract` executable to create page-level OCR output. In normal Python
installs, `tesseract` must be installed separately and available on `PATH`.
If OCR is needed and Tesseract cannot be found, `docflow` fails before page
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

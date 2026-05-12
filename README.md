# docflow

Small command-line utilities for document workflows.

`docflow` is the working name for this toolkit. The current code still ships as
separate tools while the repository migrates toward one unified command.

## Use The Right Tool

Run these tools with `uv`, not `python` directly.

- From a tool directory, use `uv run <command> ...`
- For PDF page order changes or PDF merging, use `pdftools`
- For JPEG-to-PDF conversion, use `jpg2pdf`
- For OCR on existing PDFs, use `batch-ocr`

## Included tools

### `pdftools`

PDF page operations:
- reverse page order
- join multiple PDFs
- split one PDF into multiple parts

Run from `pdftools/` with `uv run pdftools ...`.

See `pdftools/README.md` for commands and examples.

### `jpg2pdf`

Combine sequentially numbered JPEG files into PDFs, grouped by filename prefix.

Run from `jpeg2pdf/` with `uv run jpg2pdf ...`.

See `jpeg2pdf/README.md` for usage.

### `batch-ocr`

Recursively OCR PDF files in directories.

Run from `batch-ocr/` with `uv run batch-ocr ...`.

See `batch-ocr/README.md` for usage.

## Reverse And Combine PDFs

Use `pdftools`, not `jpg2pdf` or `batch-ocr`.

```bash
cd pdftools
uv run pdftools reverse file1.pdf
uv run pdftools reverse file2.pdf
uv run pdftools join combined.pdf file1_reversed.pdf file2_reversed.pdf
```

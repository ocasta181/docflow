# docflow

Small command-line utilities for document workflows.

`docflow` is the working name for this toolkit. The current code still ships as
one unified command with legacy aliases for the original tool names.

## Use The Right Tool

Run these tools with `uv`, not `python` directly.

- For PDF page order changes or PDF merging, use `uv run docflow pdf ...`
- For JPEG-to-PDF conversion, use `uv run docflow image to-pdf ...`
- For OCR on existing PDFs, use `uv run docflow ocr ...`
- The legacy aliases `pdftools`, `jpg2pdf`, and `batch-ocr` still work during
  migration.

## Included tools

### `pdftools`

PDF page operations:
- reverse page order
- join multiple PDFs
- split one PDF into multiple parts

Run with `uv run docflow pdf ...`.

See `pdftools/README.md` for commands and examples.

### `jpg2pdf`

Combine sequentially numbered JPEG files into PDFs, grouped by filename prefix.

Run with `uv run docflow image to-pdf ...`.

See `jpeg2pdf/README.md` for usage.

### `batch-ocr`

Recursively OCR PDF files in directories.

Run with `uv run docflow ocr ...`.

See `batch-ocr/README.md` for usage.

## Reverse And Combine PDFs

Use `docflow pdf`, not `docflow image` or `docflow ocr`.

```bash
uv run docflow pdf reverse file1.pdf
uv run docflow pdf reverse file2.pdf
uv run docflow pdf join combined.pdf file1_reversed.pdf file2_reversed.pdf
```

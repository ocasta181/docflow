# pdftools

Small command-line PDF utilities for non-destructive page operations.

## Use The Correct Runner

Run this tool with `uv`.

```bash
cd /Users/ocasta/Code/utils/pdftools
uv run pdftools --help
```

Use `pdftools` for:
- reversing PDF page order
- joining existing PDFs
- splitting PDFs into parts

Do not use `jpg2pdf` or `batch-ocr` for these page-order and merge operations.

## Commands

### Reverse a PDF

```bash
uv run pdftools reverse input.pdf
```

This writes `input_reversed.pdf` next to the original file.

You can also choose the output name explicitly:

```bash
uv run pdftools reverse input.pdf --output reversed.pdf
```

### Join PDFs

```bash
uv run pdftools join combined.pdf first.pdf second.pdf
```

The input order is preserved in the combined output.

### Split a PDF

```bash
uv run pdftools split input.pdf --parts 3
```

## Reverse Two PDFs And Combine Them

If you need each document reversed before combining them:

```bash
uv run pdftools reverse file1.pdf
uv run pdftools reverse file2.pdf
uv run pdftools join combined.pdf file1_reversed.pdf file2_reversed.pdf
```

This keeps the original PDFs unchanged.

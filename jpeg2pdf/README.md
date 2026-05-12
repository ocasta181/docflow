# jpg2pdf

Combine sequentially numbered JPEG files into PDFs, grouped by filename prefix.

## Use The Correct Runner

Run this tool with `uv`.

```bash
cd /Users/ocasta/Code/utils/jpeg2pdf
uv run jpg2pdf --help
```

Use `jpg2pdf` for JPEG image sets that should become PDFs.

Do not use this tool for:
- reversing PDF page order
- merging existing PDFs
- OCR on PDFs

For those workflows, use `pdftools` or `batch-ocr` instead.

## Common Usage

Process the current directory:

```bash
uv run jpg2pdf
```

Process a specific directory:

```bash
uv run jpg2pdf /path/to/scans
```

Process only one prefix:

```bash
uv run jpg2pdf /path/to/scans --prefix tax_return
```

Write PDFs to a custom output directory:

```bash
uv run jpg2pdf /path/to/scans --output /path/to/output
```

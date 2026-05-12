# batch-ocr

Recursively OCR PDF files in directories.

## Use The Correct Runner

Run this tool with `uv`.

```bash
cd /Users/ocasta/Code/utils/batch-ocr
uv run batch-ocr --help
```

Use `batch-ocr` for adding OCR text to existing PDFs or extracting text from them.

Do not use this tool for:
- reversing PDF page order
- merging PDFs
- converting JPEG sequences into PDFs

For those workflows, use `pdftools` or `jpg2pdf` instead.

## Common Usage

OCR one PDF:

```bash
uv run batch-ocr /path/to/file.pdf
```

OCR all PDFs in a directory tree:

```bash
uv run batch-ocr /path/to/folder
```

Preview what would be processed:

```bash
uv run batch-ocr /path/to/folder --dry-run
```

Extract text files, running OCR first if needed:

```bash
uv run batch-ocr /path/to/folder --extract
```

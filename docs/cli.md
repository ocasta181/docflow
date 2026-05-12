# CLI Reference

Generated from the current `docflow` command help.

## `docflow`

```text
usage: docflow [-h] [--version] {image,ocr,pdf} ...

Document workflow utilities

positional arguments:
  {image,ocr,pdf}
    image          Image document workflows
    ocr            OCR and text extraction
    pdf            PDF page operations

options:
  -h, --help       show this help message and exit
  --version        Show the installed version and exit
```

## `docflow pdf`

```text
usage: docflow pdf [-h] {reverse,join,split} ...

positional arguments:
  {reverse,join,split}
    reverse             Reverse the page order of a PDF
    join                Join multiple PDFs into one
    split               Split a PDF into multiple parts

options:
  -h, --help            show this help message and exit
```

## `docflow pdf reverse`

```text
usage: docflow pdf reverse [-h] [--output OUTPUT] input

positional arguments:
  input                 Input PDF file

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output PDF file (default: INPUTNAME_reversed.pdf)
```

## `docflow pdf join`

```text
usage: docflow pdf join [-h] output inputs [inputs ...]

positional arguments:
  output      Output PDF file
  inputs      Input PDF files to join

options:
  -h, --help  show this help message and exit
```

## `docflow pdf split`

```text
usage: docflow pdf split [-h] [--parts PARTS] input

positional arguments:
  input                 Input PDF file

options:
  -h, --help            show this help message and exit
  --parts PARTS, -n PARTS
                        Number of parts to split into (default: 2)
```

## `docflow image`

```text
usage: docflow image [-h] {to-pdf} ...

positional arguments:
  {to-pdf}
    to-pdf    Combine sequentially-numbered JPEG files into PDFs

options:
  -h, --help  show this help message and exit
```

## `docflow image to-pdf`

```text
usage: docflow image to-pdf [-h] [--prefix PREFIX] [--output OUTPUT]
                            [directory]

positional arguments:
  directory             Directory to scan (default: current directory)

options:
  -h, --help            show this help message and exit
  --prefix PREFIX, -p PREFIX
                        Only process files matching this prefix (case-
                        insensitive)
  --output OUTPUT, -o OUTPUT
                        Output directory (default: ./pdfs/)
```

## `docflow ocr`

```text
usage: docflow ocr [-h] {run,extract} ...

positional arguments:
  {run,extract}
    run          Run OCR on PDF files
    extract      Extract PDF text to .txt files

options:
  -h, --help     show this help message and exit
```

## `docflow ocr run`

```text
usage: docflow ocr run [-h] [--no-recursive] [--dry-run] [--quiet]
                       [--lang LANG] [--force] [--output OUTPUT]
                       [--output-dir OUTPUT_DIR]
                       path

positional arguments:
  path                  Directory to process (or single PDF file)

options:
  -h, --help            show this help message and exit
  --no-recursive, -n    Don't process subdirectories
  --dry-run, -d         Show what would be processed without making changes
  --quiet, -q           Only show errors and summary
  --lang LANG           Tesseract language code(s) to use when OCR is needed
                        (default: eng)
  --force, -f           Run OCR even on files that already have text
  --output OUTPUT, -o OUTPUT
                        Output PDF file for a single input PDF
  --output-dir OUTPUT_DIR
                        Output directory for OCR PDFs when processing a
                        directory
```

## `docflow ocr extract`

```text
usage: docflow ocr extract [-h] [--no-recursive] [--dry-run] [--quiet]
                           [--lang LANG]
                           path

positional arguments:
  path                Directory to process (or single PDF file)

options:
  -h, --help          show this help message and exit
  --no-recursive, -n  Don't process subdirectories
  --dry-run, -d       Show what would be processed without making changes
  --quiet, -q         Only show errors and summary
  --lang LANG         Tesseract language code(s) to use when OCR is needed
                      (default: eng)
```

# CLI Reference

Generated from the current `pliage` command help.

## `pliage`

```text
usage: pliage [-h] [--version] {image,ocr,pdf} ...

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

## `pliage pdf`

```text
usage: pliage pdf [-h] {reverse,join,split} ...

positional arguments:
  {reverse,join,split}
    reverse             Reverse the page order of a PDF
    join                Join multiple PDFs into one
    split               Split a PDF into multiple parts

options:
  -h, --help            show this help message and exit
```

## `pliage pdf reverse`

```text
usage: pliage pdf reverse [-h] [--output OUTPUT] [--json] input

positional arguments:
  input                Input PDF file

options:
  -h, --help           show this help message and exit
  --output, -o OUTPUT  Output PDF file (default: INPUTNAME_reversed.pdf)
  --json               Emit machine-readable JSON output
```

## `pliage pdf join`

```text
usage: pliage pdf join [-h] [--json] output inputs [inputs ...]

positional arguments:
  output      Output PDF file
  inputs      Input PDF files to join

options:
  -h, --help  show this help message and exit
  --json      Emit machine-readable JSON output
```

## `pliage pdf split`

```text
usage: pliage pdf split [-h] [--parts PARTS] [--json] input

positional arguments:
  input              Input PDF file

options:
  -h, --help         show this help message and exit
  --parts, -n PARTS  Number of parts to split into (default: 2)
  --json             Emit machine-readable JSON output
```

## `pliage image`

```text
usage: pliage image [-h] {to-pdf,to-bw} ...

positional arguments:
  {to-pdf,to-bw}
    to-pdf        Combine sequentially-numbered JPEG or PNG files into PDFs
    to-bw         Convert images to black-and-white (grayscale) PNGs

options:
  -h, --help      show this help message and exit
```

## `pliage image to-pdf`

```text
usage: pliage image to-pdf [-h] [--prefix PREFIX] [--output OUTPUT] [--json]
                           [directory]

positional arguments:
  directory            Directory to scan (default: current directory)

options:
  -h, --help           show this help message and exit
  --prefix, -p PREFIX  Only process files matching this prefix (case-
                       insensitive)
  --output, -o OUTPUT  Output directory (default: ./pdfs/)
  --json               Emit machine-readable JSON output
```

## `pliage image to-bw`

```text
usage: pliage image to-bw [-h] [--output OUTPUT] [--dpi DPI] [--detect-size]
                          [--grid [SIZE]] [--json]
                          [directory]

positional arguments:
  directory            Directory containing images (default: current
                       directory)

options:
  -h, --help           show this help message and exit
  --output, -o OUTPUT  Output directory (default: overwrite in place as PNG)
  --dpi DPI            Target output resolution in DPI/PPI (e.g. 150)
  --detect-size        Measure true resolution from a reference grid instead
                       of assuming page size
  --grid [SIZE]        Grid-square size for --detect-size (e.g. 1cm, 5mm,
                       0.5in; default 1cm)
  --json               Emit machine-readable JSON output
```

## `pliage ocr`

```text
usage: pliage ocr [-h] {run,extract} ...

positional arguments:
  {run,extract}
    run          Run OCR on PDF files
    extract      Extract PDF text to .txt files

options:
  -h, --help     show this help message and exit
```

## `pliage ocr run`

```text
usage: pliage ocr run [-h] [--no-recursive] [--dry-run] [--quiet]
                      [--lang LANG] [--json] [--force] [--output OUTPUT]
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
  --json                Emit machine-readable JSON output
  --force, -f           Run OCR even on files that already have text
  --output, -o OUTPUT   Output PDF file for a single input PDF
  --output-dir OUTPUT_DIR
                        Output directory for OCR PDFs when processing a
                        directory
```

## `pliage ocr extract`

```text
usage: pliage ocr extract [-h] [--no-recursive] [--dry-run] [--quiet]
                          [--lang LANG] [--json]
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
  --json              Emit machine-readable JSON output
```

# JSON Output

Commands that accept `--json` write exactly one JSON object to stdout and do
not print human progress text. On known command failures, the process returns
exit code `1` and the JSON object contains `success: false`.

Paths are serialized as strings. Object keys are sorted for stable diffs, but
callers should read fields by name instead of relying on key order.

## Common Error Shape

```json
{
  "error": "File not found: input.pdf",
  "success": false
}
```

Missing optional dependencies include an additional `missing_dependency` object:

```json
{
  "error": "Missing optional dependency: pypdf. Install with `pliage[pdf]` or `pliage[all]`.",
  "missing_dependency": {
    "extra": "pdf",
    "package": "pypdf"
  },
  "success": false
}
```

## PDF Commands

`pliage pdf reverse INPUT --json`

```json
{
  "command": "pdf reverse",
  "input": "input.pdf",
  "output": "input_reversed.pdf",
  "pages": 2,
  "success": true
}
```

`pliage pdf join OUTPUT INPUT... --json`

```json
{
  "command": "pdf join",
  "inputs": [
    {
      "pages": 1,
      "path": "first.pdf"
    }
  ],
  "output": "joined.pdf",
  "pages": 1,
  "success": true
}
```

`pliage pdf split INPUT --json`

```json
{
  "command": "pdf split",
  "input": "input.pdf",
  "pages": 4,
  "parts": [
    {
      "end_page": 2,
      "path": "input_part1.pdf",
      "start_page": 1
    }
  ],
  "success": true
}
```

## Image Commands

`pliage image to-pdf DIRECTORY --json`

```json
{
  "command": "image to-pdf",
  "results": [
    {
      "image_count": 2,
      "output_path": "pdfs/scan.pdf",
      "prefix": "scan"
    }
  ],
  "success": true,
  "warnings": []
}
```

Warnings are non-fatal and do not change `success` by themselves.

## OCR Commands

`pliage ocr run PATH --json`

Single-file output:

```json
{
  "command": "ocr run",
  "result": {
    "message": "Already has text",
    "output_path": null,
    "path": "text.pdf",
    "skipped": true,
    "success": true
  },
  "success": true
}
```

Directory output:

```json
{
  "command": "ocr run",
  "results": [
    {
      "message": "OCR completed",
      "output_path": "ocr-pdfs/scan.pdf",
      "path": "scan.pdf",
      "skipped": false,
      "success": true
    }
  ],
  "success": true,
  "summary": {
    "errors": 0,
    "processed": 1,
    "skipped": 0
  }
}
```

`pliage ocr extract PATH --json`

Single-file output:

```json
{
  "command": "ocr extract",
  "result": {
    "message": "Extracted existing text",
    "ocr_performed": false,
    "output_path": "text.txt",
    "path": "text.pdf",
    "success": true
  },
  "success": true
}
```

Directory output:

```json
{
  "command": "ocr extract",
  "results": [
    {
      "message": "Extracted existing text",
      "ocr_performed": false,
      "output_path": "text.txt",
      "path": "text.pdf",
      "success": true
    }
  ],
  "success": true,
  "summary": {
    "errors": 0,
    "extracted": 1,
    "ocrd": 0
  }
}
```

Dry runs include `dry_run: true` and list planned inputs instead of results.

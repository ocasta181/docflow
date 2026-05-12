# Changelog

## Unreleased

- Added CI coverage for linting, formatting, tests, builds, and wheel smoke
  tests.
- Added `docflow --version`.
- Added clearer optional dependency errors for installs without feature extras.
- Added a Tesseract preflight error for OCR work that needs OCR.
- Added non-destructive OCR output options with `--output` and `--output-dir`.
- Removed the old duplicated per-tool source trees from `main`.

## 0.1.0 - 2026-05-12

- Introduced the unified `docflow` command with `pdf`, `image`, and `ocr`
  subcommands.
- Preserved `pdftools`, `jpg2pdf`, and `batch-ocr` as compatibility aliases.
- Consolidated packaging into one root `pyproject.toml`, one `uv.lock`, and one
  root `justfile`.
- Added MIT license metadata.
- Added release-facing README documentation.
- Tagged the first repository release.

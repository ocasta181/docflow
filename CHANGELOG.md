# Changelog

## Unreleased

- Removed temporary compatibility entry points and the `pliage.legacy` package.
  The only public executable is `pliage`.

## 0.1.1 - 2026-05-12

- Added CI coverage for linting, formatting, tests, builds, and wheel smoke
  tests.
- Added `pliage --version`.
- Added clearer optional dependency errors for installs without feature extras.
- Added a Tesseract preflight error for OCR work that needs OCR.
- Added non-destructive OCR output options with `--output` and `--output-dir`.
- Added OCR language selection with `--lang`.
- Added structured `--json` output and documented the scripting contract.
- Added type-checking configuration and a `py.typed` marker.
- Added generated CLI reference documentation.
- Added release automation, publishing documentation, and PyPI Trusted
  Publishing wiring.
- Added dedicated OCR integration coverage in CI.
- Renamed the project, repository target, distribution package, import package,
  and primary executable to `pliage` because `docflow` is already registered on
  PyPI.
- Removed the old duplicated per-tool source trees from `main`.

## 0.1.0 - 2026-05-12

- Introduced the unified `pliage` command with `pdf`, `image`, and `ocr`
  subcommands.
- Consolidated packaging into one root `pyproject.toml`, one `uv.lock`, and one
  root `justfile`.
- Added MIT license metadata.
- Added release-facing README documentation.
- Tagged the first repository release.

# Architecture

`pliage` should be a small document-workflow toolkit with one user-facing
CLI and separate domain modules underneath it. The CLI should make common
workflows easy to discover without forcing unrelated capabilities into the same
implementation module.

## Goals

- Provide one obvious command for document workflows.
- Keep PDF operations, image-to-PDF conversion, and OCR as separate domains.
- Share infrastructure for CLI behavior, filesystem safety, output handling,
  and build/test tooling.
- Keep optional or heavy dependencies isolated from lightweight operations.
- Preserve simple standalone workflows for local personal use and automation.

## Public Interface

The project should ship a single primary executable:

```bash
pliage <domain> <command> [options]
```

The top-level command should route to domain-specific subcommands:

```bash
pliage pdf reverse input.pdf
pliage pdf join output.pdf first.pdf second.pdf
pliage pdf split input.pdf --parts 3

pliage image to-pdf /path/to/scans --prefix tax_return

pliage ocr run /path/to/file-or-folder
pliage ocr extract /path/to/file-or-folder
```

The public interface is the single `pliage` command. Commands should support
`--json` where script consumers need stable, machine-readable output without
scraping human progress text. The JSON shapes should be documented as a public
scripting contract.

## Domains

The code should be organized by domain:

```text
src/pliage/
  cli/
    app.py
    errors.py
    output.py
  shared/
    files.py
    pdf.py
    results.py
    temp.py
  domains/
    pdf/
      models.py
      service.py
      router.py
    image_pdf/
      models.py
      service.py
      router.py
    ocr/
      models.py
      service.py
      router.py
      tesseract.py
```

Routers should parse CLI input, call one service function, and format output.
Services should own workflow behavior. Shared modules should contain only
cross-cutting utilities that are used by more than one domain.

## Dependency Boundaries

Dependencies should stay as narrow as possible:

- `pdf` domain: `pypdf`
- `image_pdf` domain: `Pillow`, `reportlab` or a chosen PDF image backend
- `ocr` domain: `PyMuPDF`, Tesseract subprocess integration
- `cli` and `shared`: standard library first

The package should use optional dependency groups so lightweight PDF operations
do not require OCR dependencies:

```toml
[project.optional-dependencies]
pdf = ["pypdf>=4.0"]
image = ["Pillow>=10.0", "reportlab>=4.0"]
ocr = ["pymupdf>=1.24"]
all = ["pypdf>=4.0", "Pillow>=10.0", "reportlab>=4.0", "pymupdf>=1.24"]
dev = ["pytest>=8.0", "ruff>=0.8", "pyinstaller>=6.0"]
```

If a standalone binary is built, it should include the dependencies required by
that binary's enabled features. Tesseract and tessdata bundling should remain
an explicit build choice because it materially changes binary size and
platform behavior.

## Shared Infrastructure

Shared code should cover behavior that every domain should get right once:

- path resolution and validation
- extension checks
- safe temporary files and temporary directories
- atomic output replacement for in-place operations
- output path conflict checks
- PDF page count helpers
- consistent command result models
- consistent warning, error, summary, and quiet-mode output
- structured JSON output for script-friendly command results
- common exit-code mapping

Shared infrastructure should not contain domain business logic. For example,
page splitting belongs in the PDF domain; scan filename grouping belongs in the
image-to-PDF domain; Tesseract command discovery belongs in the OCR domain.

## Error Handling

Core services should return typed results or raise narrow domain errors. They
should not call `sys.exit()` or print directly. CLI routers should translate
results and errors into user-facing output and process exit codes.

Commands should fail loud:

- missing input paths return non-zero exit codes
- output paths must not overwrite inputs unless the command explicitly supports
  safe in-place replacement
- partial failures in batch workflows should be reported in the final summary
- skipped files should be distinguishable from failed files

## Filesystem Safety

All writes should be safe by default:

- use `TemporaryDirectory` or `NamedTemporaryFile`, not unsafe temp-name helpers
- write in-place changes to a temporary sibling and atomically replace only
  after success
- prevent output paths from matching input paths unless the service has an
  explicit safe replacement strategy
- avoid leaving partial output files when no valid pages or images were written

## Testing

Tests should verify intent at the domain boundary:

- unit tests for pure parsing, grouping, page-range calculation, and path checks
- integration-style tests for PDF creation/manipulation using real temporary
  files
- CLI tests that call command entry points with controlled arguments
- no tests that depend on a hardcoded local virtualenv path

OCR tests should separate "Tesseract is installed and works" checks from pure
service behavior. Tests that require the external binary should be marked so
they can be skipped explicitly when the dependency is absent.

## Build And Release

The repository should have one root `pyproject.toml`, one root lock file, and
one root task runner. The default developer workflow should be:

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Build artifacts should be generated into ignored directories. Source archives,
wheels, and standalone binaries should be produced from clean source state, not
from checked-in generated files.

# Root project tasks.

root_test := "uv run --extra dev --extra pdf --extra image --extra ocr pytest tests -q"

# Install root development dependencies.
setup:
    uv sync --extra dev --extra pdf --extra image --extra ocr

# Run the root docflow test suite.
test:
    {{root_test}}

# Run the legacy tool suites that still live in their old project directories.
test-legacy:
    cd pdftools && uv run pytest tests -q
    cd batch-ocr && uv run pytest tests -q
    cd jpeg2pdf && uv run --extra dev python test_jpg2pdf.py

# Run every current test suite.
test-all:
    {{root_test}}
    just test-legacy

# Lint the root package and tests.
lint:
    uv run --extra dev ruff check src tests

# Format the root package and tests.
format:
    uv run --extra dev ruff format src tests

# Build the root package.
build:
    uv build

# Clean root-generated artifacts.
clean:
    rm -rf build dist *.egg-info .pytest_cache .ruff_cache

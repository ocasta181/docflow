# Root project tasks.

root_test := "uv run --extra dev --extra pdf --extra image --extra ocr pytest tests -q"

# Install root development dependencies.
setup:
    uv sync --extra dev --extra pdf --extra image --extra ocr

# Run the root docflow test suite.
test:
    {{root_test}}

# Run every current test suite.
test-all:
    {{root_test}}

# Type-check the root package.
typecheck:
    uv run --extra dev --extra pdf --extra image --extra ocr pyright

# Lint the root package and tests.
lint:
    uv run --extra dev ruff check src tests tools

# Format the root package and tests.
format:
    uv run --extra dev ruff format src tests tools

# Check formatting without changing files.
format-check:
    uv run --extra dev ruff format --check src tests tools

# Build the root package.
build:
    uv build

# Regenerate checked-in docs from command help.
docs:
    uv run --extra dev --extra pdf --extra image --extra ocr python tools/generate_cli_docs.py

# Verify generated docs are up to date.
docs-check: docs
    git diff --exit-code docs/cli.md

# Run the full local pre-push quality gate.
check: docs-check format-check lint typecheck test-all build

# Clean root-generated artifacts.
clean:
    rm -rf build dist *.egg-info .pytest_cache .ruff_cache

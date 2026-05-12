# Architecture Migration Plan

This checklist describes a staged migration toward the target architecture.
Each stage should leave the tools working and tested.

## Stage 0: Repository Hygiene

- [x] Initialize the root git repository.
- [x] Add a root `.gitignore` for caches, virtualenvs, build outputs, and local
      settings.
- [x] Remove generated artifacts from version control if any were committed.
- [x] Confirm git commits use the `ocasta181` profile.
- [x] Run a local secrets scan before publishing.

## Stage 1: Stabilize Existing Tools

- [x] Add missing `jpg2pdf` test dependencies.
- [x] Replace `jpg2pdf`'s hardcoded `.venv/bin/python` test runner with the
      active Python interpreter or normal `pytest` entry points.
- [x] Add a `jpg2pdf` test command to its `justfile`.
- [x] Add output-path conflict checks to PDF join operations.
- [x] Replace unsafe temporary-name creation in OCR code with managed temporary
      files or directories.
- [x] Ensure OCR cleanup runs on failure paths.
- [x] Run all existing tests and record any external dependencies required.

## Stage 2: Normalize Package Shape

- [x] Convert `jpg2pdf` from a single script into a package.
- [x] Split `jpg2pdf` into `core.py` or `service.py` plus `cli.py`.
- [x] Make all command entry points return integer exit codes instead of calling
      `sys.exit()` inside testable functions.
- [x] Keep existing `pdftools`, `jpg2pdf`, and `batch-ocr` commands working.
- [x] Add CLI tests for the normalized `jpg2pdf` command.

## Stage 3: Introduce Shared Infrastructure

- [x] Add shared path validation helpers.
- [x] Add shared safe temporary file/directory helpers.
- [x] Add shared output conflict checks.
- [x] Add shared command result and summary models.
- [ ] Move duplicated page-count and file-discovery behavior into shared
      modules only where two or more domains use it.
- [x] Keep domain-specific behavior inside domain modules.

## Stage 4: Create Unified CLI

- [x] Add a new root package under `src/docflow`.
- [x] Add the `docflow` executable.
- [x] Add the `pdf` subcommand group.
- [ ] Add the `image` and `ocr` subcommand groups.
- [x] Route `docflow pdf reverse|join|split` to the PDF domain service.
- [ ] Route `docflow image to-pdf` to the image-to-PDF domain service.
- [ ] Route `docflow ocr run|extract` to the OCR domain service.
- [ ] Add top-level help text that makes command choice obvious.
- [ ] Keep legacy commands as wrappers while migration is incomplete.

## Stage 5: Consolidate Tooling

- [ ] Replace per-tool `pyproject.toml` files with one root `pyproject.toml`.
- [ ] Define optional dependency groups for `pdf`, `image`, `ocr`, `all`, and
      `dev`.
- [ ] Move to one root `uv.lock`.
- [ ] Add one root `justfile` with `setup`, `test`, `lint`, `format`, `build`,
      and `clean` tasks.
- [ ] Run the full test suite from the repository root.

## Stage 6: Release Preparation

- [ ] Decide package and executable names before publishing.
- [ ] Add license metadata.
- [ ] Add project URLs and supported Python versions.
- [ ] Add a release README focused on installation and usage.
- [ ] Document external OCR requirements and standalone-binary behavior.
- [ ] Build a wheel from a clean checkout.
- [ ] Install the wheel in a fresh environment and smoke-test each command.
- [ ] Run a final secrets scan.
- [ ] Tag the first release.

## Stage 7: Remove Migration Shims

- [ ] Decide whether legacy executables remain supported aliases.
- [ ] Remove compatibility wrappers that are not part of the public interface.
- [ ] Delete obsolete per-tool build files.
- [ ] Delete obsolete specs after their behavior is covered by tests and docs.
- [ ] Update migration docs with completed decisions.

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
- [x] Move duplicated page-count and file-discovery behavior into shared
      modules only where two or more domains use it.
- [x] Keep domain-specific behavior inside domain modules.

## Stage 4: Create Unified CLI

- [x] Add a new root package under `src/docflow_cli`.
- [x] Add the `docflow` executable.
- [x] Add the `pdf` subcommand group.
- [x] Add the `image` subcommand group.
- [x] Add the `ocr` subcommand group.
- [x] Route `docflow pdf reverse|join|split` to the PDF domain service.
- [x] Route `docflow image to-pdf` to the image-to-PDF domain service.
- [x] Route `docflow ocr run|extract` to the OCR domain service.
- [x] Add top-level help text that makes command choice obvious.
- [x] Keep legacy commands as wrappers while migration is incomplete.

## Stage 5: Consolidate Tooling

- [x] Replace per-tool `pyproject.toml` files with one root `pyproject.toml`.
- [x] Define optional dependency groups for `pdf`, `image`, `ocr`, `all`, and
      `dev`.
- [x] Move to one root `uv.lock`.
- [x] Add one root `justfile` with `setup`, `test`, `lint`, `format`, `build`,
      and `clean` tasks.
- [x] Run the full test suite from the repository root.

## Stage 6: Release Preparation

- [x] Decide package and executable names before publishing.
- [x] Add license metadata.
- [x] Add project URLs and supported Python versions.
- [x] Add a release README focused on installation and usage.
- [x] Document external OCR requirements and standalone-binary behavior.
- [x] Build a wheel from a clean checkout.
- [x] Install the wheel in a fresh environment and smoke-test each command.
- [x] Run a final secrets scan.
- [x] Tag the first release.

## Stage 7: Remove Migration Shims

- [x] Decide whether legacy executables remain supported aliases.
- [x] Remove compatibility wrappers that are not part of the public interface.
- [x] Delete obsolete per-tool build files.
- [x] Delete obsolete specs after their behavior is covered by tests and docs.
- [x] Update migration docs with completed decisions.

## Stage 8: Post-Migration Hardening

- [x] Add CI for lint, format checks, tests, build, and wheel smoke tests.
- [x] Add a `docflow --version` command backed by package metadata.
- [x] Add no-extra install tests for missing `pdf`, `image`, and `ocr`
      optional dependencies.
- [x] Add a clear Tesseract preflight error for OCR work that actually needs
      OCR.
- [x] Make destructive OCR writes explicit, or add non-destructive output
      options.
- [x] Narrow broad exception handling where errors are currently swallowed or
      flattened.
- [x] Add type-checking configuration and a `py.typed` marker.
- [x] Add a changelog now that `v0.1.0` exists.
- [x] Add release automation for tagged builds and release notes.
- [x] Generate or maintain CLI reference documentation from command help.
- [x] Add structured output support for scripting if real automation needs it.
- [x] Add OCR language selection.

## Stage 9: Publishing Polish

- [x] Make top-level optional dependency errors respect `--json`.
- [x] Add a single local quality-gate command for pre-push verification.
- [x] Check generated CLI documentation in CI.
- [x] Add a short publishing runbook for tags, releases, and package upload.

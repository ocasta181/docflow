"""CLI router for OCR workflows."""

import argparse
import sys
from pathlib import Path


def register_ocr_parser(subparsers: argparse._SubParsersAction) -> None:
    ocr_parser = subparsers.add_parser("ocr", help="OCR and text extraction")
    ocr_subparsers = ocr_parser.add_subparsers(dest="ocr_command", required=True)

    run_parser = ocr_subparsers.add_parser("run", help="Run OCR on PDF files")
    _add_common_arguments(run_parser)
    run_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Run OCR even on files that already have text",
    )
    run_parser.set_defaults(handler=cmd_run)

    extract_parser = ocr_subparsers.add_parser("extract", help="Extract PDF text to .txt files")
    _add_common_arguments(extract_parser)
    extract_parser.set_defaults(handler=cmd_extract)


def cmd_run(args: argparse.Namespace) -> int:
    from .service import find_pdfs, ocr_pdf

    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    if path.is_file():
        if path.suffix.lower() != ".pdf":
            print(f"Error: Not a PDF file: {path}", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"Would process: {path}")
            return 0
        print(f"Processing: {path}")
        result = ocr_pdf(path, skip_if_text=not args.force)
        return _print_ocr_single_result(result)

    recursive = not args.no_recursive
    pdfs = find_pdfs(path, recursive)
    if not pdfs:
        print(f"No PDF files found in {path}")
        return 0

    if args.dry_run:
        print(f"Found {len(pdfs)} PDF file(s) to process in {path}:")
        for pdf in pdfs:
            print(f"  {pdf.relative_to(path)}")
        return 0

    print(f"Processing {len(pdfs)} PDF file(s) in {path}")
    print()

    results = []
    for index, pdf_path in enumerate(pdfs):
        result = ocr_pdf(pdf_path, skip_if_text=not args.force)
        results.append(result)
        if not args.quiet:
            rel_path = pdf_path.relative_to(path)
            if result.skipped:
                print(f"[{index + 1}/{len(pdfs)}] {rel_path} - skipped ({result.message})")
            elif result.success:
                print(f"[{index + 1}/{len(pdfs)}] {rel_path} - OCR completed")
            else:
                print(
                    f"[{index + 1}/{len(pdfs)}] {rel_path} - ERROR: {result.message}",
                    file=sys.stderr,
                )

    if not args.quiet:
        print()

    processed = sum(1 for result in results if result.success and not result.skipped)
    skipped = sum(1 for result in results if result.skipped)
    errors = sum(1 for result in results if not result.success)
    print(f"Done: {processed} OCR'd, {skipped} skipped, {errors} errors")
    return 1 if errors else 0


def cmd_extract(args: argparse.Namespace) -> int:
    from .service import extract_text, find_pdfs

    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    if path.is_file():
        if path.suffix.lower() != ".pdf":
            print(f"Error: Not a PDF file: {path}", file=sys.stderr)
            return 1
        if args.dry_run:
            print(f"Would extract text from: {path}")
            return 0
        print(f"Processing: {path}")
        result = extract_text(path, ocr_if_needed=True)
        return _print_extract_single_result(result)

    recursive = not args.no_recursive
    pdfs = find_pdfs(path, recursive)
    if not pdfs:
        print(f"No PDF files found in {path}")
        return 0

    if args.dry_run:
        print(f"Found {len(pdfs)} PDF file(s) to extract text from in {path}:")
        for pdf in pdfs:
            print(f"  {pdf.relative_to(path)}")
        return 0

    print(f"Extracting text from {len(pdfs)} PDF file(s) in {path}")
    print()

    results = []
    for index, pdf_path in enumerate(pdfs):
        result = extract_text(pdf_path, ocr_if_needed=True)
        results.append(result)
        if not args.quiet:
            rel_path = pdf_path.relative_to(path)
            if result.success:
                status = "OCR'd + extracted" if result.ocr_performed else "extracted"
                print(f"[{index + 1}/{len(pdfs)}] {rel_path} - {status}")
            else:
                print(
                    f"[{index + 1}/{len(pdfs)}] {rel_path} - ERROR: {result.message}",
                    file=sys.stderr,
                )

    if not args.quiet:
        print()

    extracted = sum(1 for result in results if result.success and not result.ocr_performed)
    ocrd = sum(1 for result in results if result.success and result.ocr_performed)
    errors = sum(1 for result in results if not result.success)
    print(f"Done: {extracted} extracted, {ocrd} OCR'd + extracted, {errors} errors")
    return 1 if errors else 0


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", help="Directory to process (or single PDF file)")
    parser.add_argument(
        "--no-recursive",
        "-n",
        action="store_true",
        help="Don't process subdirectories",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be processed without making changes",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors and summary",
    )


def _print_ocr_single_result(result) -> int:
    if result.skipped:
        print(f"  Skipped: {result.message}")
        return 0
    if result.success:
        print(f"  Done: {result.message}")
        return 0
    print(f"  Error: {result.message}", file=sys.stderr)
    return 1


def _print_extract_single_result(result) -> int:
    if result.success:
        status = "OCR'd and extracted" if result.ocr_performed else "extracted"
        print(f"  {status} -> {result.output_path}")
        return 0
    print(f"  Error: {result.message}", file=sys.stderr)
    return 1

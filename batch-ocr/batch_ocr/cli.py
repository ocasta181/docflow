"""Command-line interface for batch-ocr."""

import argparse
import sys
from pathlib import Path

from .core import ocr_pdf, find_pdfs, extract_text


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Recursively OCR PDF files in directories"
    )
    parser.add_argument(
        "path",
        help="Directory to process (or single PDF file)",
    )
    parser.add_argument(
        "--no-recursive",
        "-n",
        action="store_true",
        help="Don't process subdirectories",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Run OCR even on files that already have text",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be processed without running OCR",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors and summary",
    )
    parser.add_argument(
        "--extract",
        "-e",
        action="store_true",
        help="Extract text to .txt files (runs OCR first if needed)",
    )

    args = parser.parse_args()
    path = Path(args.path).resolve()

    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        return 1

    # Handle single file
    if path.is_file():
        if not path.suffix.lower() == ".pdf":
            print(f"Error: Not a PDF file: {path}", file=sys.stderr)
            return 1

        if args.dry_run:
            action = "extract text from" if args.extract else "process"
            print(f"Would {action}: {path}")
            return 0

        print(f"Processing: {path}")

        if args.extract:
            result = extract_text(path, ocr_if_needed=True)
            if result.success:
                status = "OCR'd and extracted" if result.ocr_performed else "extracted"
                print(f"  {status} -> {result.output_path}")
            else:
                print(f"  Error: {result.message}", file=sys.stderr)
                return 1
        else:
            result = ocr_pdf(path, skip_if_text=not args.force)
            if result.skipped:
                print(f"  Skipped: {result.message}")
            elif result.success:
                print(f"  Done: {result.message}")
            else:
                print(f"  Error: {result.message}", file=sys.stderr)
                return 1

        return 0

    # Handle directory
    recursive = not args.no_recursive
    pdfs = find_pdfs(path, recursive)

    if not pdfs:
        print(f"No PDF files found in {path}")
        return 0

    if args.dry_run:
        action = "extract text from" if args.extract else "process"
        print(f"Found {len(pdfs)} PDF file(s) to {action} in {path}:")
        for pdf in pdfs:
            print(f"  {pdf.relative_to(path)}")
        return 0

    action = "Extracting text from" if args.extract else "Processing"
    print(f"{action} {len(pdfs)} PDF file(s) in {path}")
    print()

    results = []
    for i, pdf_path in enumerate(pdfs):
        rel_path = pdf_path.relative_to(path)

        if args.extract:
            result = extract_text(pdf_path, ocr_if_needed=True)
            results.append(result)

            if not args.quiet:
                if result.success:
                    status = "OCR'd + extracted" if result.ocr_performed else "extracted"
                    print(f"[{i + 1}/{len(pdfs)}] {rel_path} - {status}")
                else:
                    print(f"[{i + 1}/{len(pdfs)}] {rel_path} - ERROR: {result.message}", file=sys.stderr)
        else:
            result = ocr_pdf(pdf_path, skip_if_text=not args.force)
            results.append(result)

            if not args.quiet:
                if result.skipped:
                    print(f"[{i + 1}/{len(pdfs)}] {rel_path} - skipped ({result.message})")
                elif result.success:
                    print(f"[{i + 1}/{len(pdfs)}] {rel_path} - OCR completed")
                else:
                    print(f"[{i + 1}/{len(pdfs)}] {rel_path} - ERROR: {result.message}", file=sys.stderr)

    if not args.quiet:
        print()

    errors = sum(1 for r in results if not r.success)

    if args.extract:
        extracted = sum(1 for r in results if r.success and not r.ocr_performed)
        ocrd = sum(1 for r in results if r.success and r.ocr_performed)
        print(f"Done: {extracted} extracted, {ocrd} OCR'd + extracted, {errors} errors")
    else:
        processed = sum(1 for r in results if r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)
        print(f"Done: {processed} OCR'd, {skipped} skipped, {errors} errors")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

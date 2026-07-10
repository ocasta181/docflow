# Why Pliage Exists

`pliage` exists because everyday document cleanup is usually a workflow, not a
single PDF operation. A common local task might start with camera or scanner
images, continue through PDF assembly and page cleanup, then end with OCR,
text extraction, or a script that needs stable JSON output. The public tooling
landscape has strong tools for each individual step, but the handoff between
those tools is where small personal workflows become brittle.

The project is intentionally narrow: one local command, a few document domains,
and predictable behavior that can be used both by a person at a terminal and by
a small automation script.

## Current Project Shape

`pliage` is a Python command-line toolkit with one primary executable:

```bash
pliage <domain> <command> [options]
```

The current domains are:

- `pliage pdf`: reverse page order, join PDFs, and split a PDF into equal
  parts.
- `pliage image to-pdf`: scan a directory for sequential image names like
  `invoice_001.jpg`, group them by prefix, warn about sequence gaps, apply EXIF
  orientation, flatten transparent images onto white, and create PDFs.
- `pliage ocr`: run OCR on PDFs, skip files that already appear to have text
  unless forced, choose Tesseract languages, write to explicit output paths,
  and extract text to `.txt` files.

The implementation follows the same boundary as the CLI: PDF behavior,
image-to-PDF behavior, and OCR behavior live in separate domain modules. Shared
code handles common concerns such as path validation, safe temporary files,
atomic replacement, output conflict checks, command summaries, and JSON output.

That shape matters because this is not trying to be a general PDF engine. It is
trying to make repeatable local document chores boring, inspectable, and safe.

## Comparable Public Tools

| Tool | What it does well | Limitation for this project use case |
| --- | --- | --- |
| [qpdf](https://qpdf.sourceforge.io/) | A mature command-line tool and C++ library for content-preserving PDF transformations. It supports splitting, merging, encryption, linearization, inspection, and detailed page selection. | It is intentionally low-level. Its project page notes that it does not render PDFs, perform text extraction, or provide high-level page-content workflows. Users still need separate tools and shell glue for scan grouping, OCR, and text extraction. |
| [Poppler utilities](https://manpages.debian.org/unstable/poppler-utils/pdfseparate.1.en.html) | Small focused commands such as `pdfseparate`, `pdfunite`, and `pdftotext`. They are widely packaged and good Unix building blocks. | The tools are separate executables with different command shapes. `pdfseparate` writes one file per extracted page and expects a printf-style output pattern, which is powerful but not the same as a user-level "split this into N parts" workflow. |
| [pdfcpu](https://github.com/pdfcpu/pdfcpu) | A broad Go PDF processor with CLI and API support for validation, optimization, splitting, trimming, merging, image/font/metadata extraction, encryption, rotation, stamps, watermarks, and more. | It is a comprehensive PDF processor. `pliage` is smaller and organized around a few end-user workflows that combine PDFs, images, OCR, and script output rather than exposing a full PDF processing surface. |
| [img2pdf](https://manpages.debian.org/testing/img2pdf/img2pdf.1.en.html) | Lossless raster-image-to-PDF conversion, especially for JPEG, PNG, and JPEG2000, with minimal file-size overhead. | It converts images that are already selected by the caller. It does not own the project-specific workflow of scanning a directory, grouping sequential files by prefix, warning about gaps, paginating tall phone captures, or emitting the same result contract as the other document commands. |
| [ImageMagick](https://imagemagick.org/command-line-processing/) | A broad image-processing toolkit that can convert and transform images from the command line, including multi-image PDF output patterns. | It is extremely capable but not document-workflow-specific. The user is responsible for choosing safe options, ordering files, grouping scans, and deciding where image processing ends and PDF/OCR handling begins. |
| [Tesseract](https://tesseract-ocr.github.io/tessdoc/) | The standard open-source OCR engine. It can be used directly from the command line, supports many languages, and can create searchable PDF output from images. | It is an OCR engine, not a document workflow manager. It expects the caller to prepare images or pages, manage PDF input/output, decide when OCR is needed, and handle batch traversal. |
| [OCRmyPDF](https://ocrmypdf.readthedocs.io/en/latest/index.html) | A strong OCR-focused PDF tool that adds searchable text layers to scanned PDFs and offers advanced behavior around existing text, large pages, cleanup, optimization, and PDF/A output. | It solves OCR deeply. `pliage` uses a smaller OCR surface and combines it with adjacent local workflows: image assembly, page operations, text extraction, and JSON output through the same CLI family. |
| [PDF Arranger](https://github.com/pdfarranger/pdfarranger) | A local desktop GUI for merging, splitting, rotating, cropping, and rearranging PDF pages, with privacy benefits over online tools. | It is interactive and visual. That is useful for manual page editing, but not ideal for repeatable terminal workflows, CI checks, or scripts that need structured output. |
| [Stirling PDF](https://docs.stirlingpdf.com/functionality/) | A large self-hosted PDF platform with many tools, including merge, split, OCR, conversion, redaction, signing, compression, and automation. | It is closer to a platform than a small utility. Running a web app or server is heavier than necessary for local one-off jobs and simple shell automation. |

## The Gap

The tools above leave three recurring gaps for this project:

1. **Workflow continuity.** PDF page operations, scan image assembly, OCR, and
   text extraction often happen together, but mature public tools usually cover
   only one layer or require the user to compose several unrelated commands.

2. **Human and script output from the same command.** Many utilities are either
   pleasant for humans or convenient for scripts. `pliage` gives commands a
   normal human output path plus `--json` where automation needs stable data.

3. **Small local defaults.** Online tools and server suites are too heavy for
   private local files. Low-level CLIs are powerful but can make routine
   document jobs feel like programming exercises. `pliage` aims for local,
   explicit, non-cloud behavior without asking the user to remember every PDF
   engine's option grammar.

## How Pliage Fills The Gap

`pliage` does not compete with qpdf, OCRmyPDF, Tesseract, img2pdf, or
ImageMagick as an engine. It sits one level above the engine layer and packages
the workflows this repository actually needs:

- A single command tree groups related document tasks without hiding the domain
  boundaries in the code.
- Optional dependency extras keep lightweight PDF tasks separate from heavier
  OCR and image dependencies.
- Legacy command aliases preserve old entry points while new scripts move to
  the `pliage` command.
- Filesystem safety is part of the service layer: output paths are checked,
  in-place writes use temporary output, and command failures report clearly.
- OCR is conservative by default: files that already appear to have text are
  skipped unless the user asks to force OCR.
- Image-to-PDF is tailored to scan batches: it understands sequential filename
  groups and warns when pages are missing.
- Structured JSON output gives automation a documented contract instead of
  forcing scripts to parse progress text.

The result is a small toolkit that is easier to explain than a shell script
folder and easier to automate than a GUI.

## What Is On The Horizon

The near-term direction is hardening, not expansion for its own sake:

- Continue tightening JSON output as a public scripting contract.
- Add only the PDF page operations that match common local workflows, such as
  extracting selected pages, deleting pages, or rotating pages, if they can be
  added without turning the tool into a full PDF editor.
- Improve scan assembly where it is already domain-specific: stronger filename
  parsing, clearer gap reports, better pagination controls, and safer handling
  of mixed image sizes.
- Keep OCR practical: better dry-run reporting, clearer Tesseract diagnostics,
  optional output-directory workflows, and more integration coverage for
  external OCR behavior.
- Decide explicitly whether standalone binaries should bundle Tesseract and
  tessdata or continue to require a system Tesseract install. That choice
  affects size, platform behavior, and release support, so it should remain a
  documented release decision.

The boundary is just as important as the roadmap. `pliage` should not become a
replacement for qpdf, OCRmyPDF, ImageMagick, or a desktop PDF editor. Its value
is being the small local layer that makes the common document workflow obvious,
safe enough for repeated use, and stable enough to script.

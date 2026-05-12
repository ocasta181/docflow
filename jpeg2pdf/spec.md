## jpg2pdf CLI Tool Specification

### Overview
A CLI tool that combines sequentially-numbered JPEG files into PDFs, grouping by filename prefix.

### Input Format
Files named: `<prefix>_<sequence>.jpg` or `<prefix>_<sequence>.jpeg`
- Prefix: any string (case-insensitive for grouping)
- Sequence: integer (not required to be zero-padded)
- Examples: `tax_return_1.jpg`, `tax_return_2.jpg`, `Birth_Certificate_1.jpeg`

### Output
- Location: `./pdfs/<prefix>.pdf`
- Create `./pdfs/` directory if it doesn't exist

### CLI Interface
```
jpg2pdf [DIRECTORY] [OPTIONS]

Arguments:
  DIRECTORY          Directory to scan (default: current directory)

Options:
  --prefix, -p       Only process files matching this prefix (case-insensitive)
  --output, -o       Output directory (default: ./pdfs/)
  --help, -h         Show help
```

### Behavior

**Grouping:**
- Case-insensitive prefix matching (`Tax_1.jpg` and `tax_2.jpg` become one PDF)
- Output filename uses the case from the first file encountered

**Sequence handling:**
- Sort numerically (so `_2` comes before `_10`)
- Warn to stderr if gaps detected: `Warning: missing sequence number(s) [3, 5] in group "tax_return"`
- Proceed with available files

**Image processing:**
- Auto-orient using EXIF orientation tag
- Fit each image to US Letter page (8.5 x 11 inches) maintaining aspect ratio
- Center image on page if it doesn't fill the page

**Page sizing:**
- Standard US Letter (612 x 792 points)
- Images scaled to fit within page margins, preserving aspect ratio

### Suggested Stack
- Python 3
- Pillow (image loading, EXIF orientation, resizing)
- img2pdf or reportlab for PDF generation (img2pdf is simpler if it handles the sizing well, otherwise reportlab gives more control)

### Example Usage
```bash
# Process all grouped JPEGs in current directory
jpg2pdf

# Process only files in ./scans/
jpg2pdf ./scans/

# Process only the "tax_return" group
jpg2pdf ./scans/ --prefix tax_return

# Custom output directory
jpg2pdf ./scans/ -o ./output/
```

### Error Handling
- Skip files that don't match the `<prefix>_<number>.jpg` pattern (log to stderr)
- Warn on sequence gaps but continue
- Error if no valid files found
- Error if image file is corrupted/unreadable (skip that file, warn, continue with group)
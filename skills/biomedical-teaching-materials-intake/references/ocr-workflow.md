# OCR Workflow

Use this workflow when `scan_materials_intake.py` classifies PDFs as `needs_ocr`.

## Preconditions

- Install `Tesseract OCR` and make sure `tesseract` is on `PATH`.
- Install `OCRmyPDF` and make sure `ocrmypdf` is on `PATH`.
- Keep the original exported PDFs and write OCR output to a separate folder.

## Recommended Command

```bash
python skills/biomedical-teaching-materials-intake/scripts/run_ocr_queue.py tmp/raonini-pdf-intake.json --source-root materials/raonini/pdf-export --output-dir materials/raonini/pdf-ocr --json-output tmp/raonini-ocr-queue.json --md-output agent-template/intake-reports/raonini-ocr-queue.md
```

This creates a machine-readable OCR queue even if OCR tools are not installed yet.

## Execute OCR When Tools Are Ready

```bash
python skills/biomedical-teaching-materials-intake/scripts/run_ocr_queue.py tmp/raonini-pdf-intake.json --source-root materials/raonini/pdf-export --output-dir materials/raonini/pdf-ocr --json-output tmp/raonini-ocr-run.json --md-output agent-template/intake-reports/raonini-ocr-run.md --execute
```

## After OCR

1. Re-run `scan_materials_intake.py` on the OCR output folder.
2. Confirm the target files are promoted from `needs_ocr` to `ready_pdf`.
3. Convert the updated intake report into retrieval candidates.
4. Merge promoted files into `retrieval-priority-v1.json`.

## Verification Checklist

- Check that the title slide and at least one dense content slide produce meaningful text.
- Check that formulas, Greek letters, and filter names are not lost.
- Keep OCR output separate from the original PDF export so failed OCR can be replaced safely.

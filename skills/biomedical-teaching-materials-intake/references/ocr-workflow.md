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

Use the post-OCR merge script to rescan the OCR output folder and automatically merge promoted files into the retrieval config:

```bash
python skills/biomedical-teaching-materials-intake/scripts/post_ocr_intake_merge.py materials/raonini/pdf-ocr --original-intake-json tmp/raonini-pdf-intake.json --retrieval-config-json agent-template/kb-v1/retrieval-priority-v1.json --retrieval-config-yaml agent-template/kb-v1/retrieval-priority-v1.yaml --retrieval-config-py agent-template/kb-v1/retrieval_priority_v1.py --rescanned-json-output tmp/raonini-pdf-ocr-intake.json --rescanned-md-output tmp/raonini-pdf-ocr-intake.md --candidate-json-output tmp/raonini-pdf-ocr-candidates.json --candidate-md-output tmp/raonini-pdf-ocr-candidates.md --merge-report-md-output agent-template/intake-reports/raonini-post-ocr-merge.md
```

This command will:

1. Re-run `scan_materials_intake.py` logic on the OCR output folder.
2. Keep only files that were previously `needs_ocr` and are now promoted to `ready_pdf` or `ready_text_source`.
3. Generate updated retrieval candidates.
4. Merge promoted files into `retrieval-priority-v1.json` and sync the YAML and Python config files.

## Verification Checklist

- Check that the title slide and at least one dense content slide produce meaningful text.
- Check that formulas, Greek letters, and filter names are not lost.
- Keep OCR output separate from the original PDF export so failed OCR can be replaced safely.

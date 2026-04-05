---
name: biomedical-teaching-materials-intake
description: Assess, normalize, and route new biomedical teaching materials into a course knowledge base. Use when Codex needs to inspect newly added course files, decide whether they are usable for retrieval, check whether a file is PDF or should be converted to PDF, determine whether a PDF is scanned and requires OCR before use, propose naming and folder placement, assign source groups such as ecg_core or eeg_core, update retrieval-priority configuration, or tell the user whether local indexes or cloud deployment need refreshing.
---

# Biomedical Teaching Materials Intake

Use this skill to standardize new course materials before they are relied on by the teaching assistant.

## Workflow

1. Inventory the new files and identify their apparent type from extension and context.
2. Decide whether each file is directly usable for retrieval.
3. Apply the PDF gate.
4. Recommend a destination folder, normalized file name, and source group.
5. Decide whether retrieval config must be updated.
6. Decide whether the local vector index must be rebuilt or the cloud app must be redeployed.
7. If OCR is required, generate an OCR queue before allowing the files into the knowledge base.

## Hard Rules

- Prefer `pdf`, `md`, `txt`, and `html` as retrieval sources.
- Treat `pptx` and `docx` as intermediate formats; recommend exporting them to `pdf` before intake.
- Do not treat a scanned PDF as knowledge-base ready until OCR is completed.
- If text extraction quality is poor, say so explicitly and lower confidence in retrieval usefulness.
- Prefer teacher-authored course materials over general public tutorials when assigning priority.
- Warn before recommending any copyrighted or source-unclear material for public repository inclusion.

## PDF Gate

When a user adds a new file, classify it into one of these states:

- `ready_pdf`: PDF with selectable, extractable text and a clear topic.
- `ready_text_source`: Markdown, text, or HTML source that is directly usable without PDF conversion.
- `needs_ocr`: PDF exists but appears scanned, image-only, or text extraction is poor.
- `convert_to_pdf`: File is usable as source material but should first be exported to PDF.
- `not_recommended`: File is too noisy, unclear, duplicated, or legally risky.

If the user provides the file itself, inspect it instead of guessing. Use the [$pdf](C:/Users/Admin/.codex/skills/pdf/SKILL.md) skill when PDF inspection or page-level checks are needed.

## What To Produce

For each intake batch, produce a compact decision list that includes:

- file name
- detected format
- intake state: `ready_pdf`, `ready_text_source`, `needs_ocr`, `convert_to_pdf`, or `not_recommended`
- recommended folder
- recommended normalized file name
- recommended source group
- whether retrieval config should change
- whether re-index or redeploy is needed
- key risk or warning

## Source Group Routing

Use the course topic, not just the file name, to place materials.

Typical groups:

- `theory_core`: sampling, filtering, FFT, STFT, wavelets, general preprocessing
- `ecg_core`: ECG morphology, QRS detection, HR/HRV, ECG labs
- `emg_core`: EMG preprocessing, envelope extraction, fatigue, activation analysis
- `hdsemg_core`: HDsEMG arrays, decomposition, gesture or motor-unit tasks
- `eeg_core`: EEG preprocessing, artifacts, spectral bands, event analysis
- `ppg_core`: PPG morphology, pulse features, wearable signal quality
- `fnirs_core`: fNIRS preprocessing, baseline drift, hemodynamic response, optical-density workflows
- `assignment_support`: assignment prompts, rubrics, FAQ, hint-oriented scaffolding
- `lab_core`: lab manuals and experiment instructions when the project uses a dedicated lab group

If a file clearly overrides older general material for the same topic, recommend moving it into a higher-priority group and demoting the older source.

## Retrieval Update Rules

Recommend updating retrieval configuration when any of the following is true:

- a new course-authored core file is added
- a file belongs to a new topic not yet represented in routing
- a stronger replacement for an existing source appears
- a lab manual or rubric should affect assignment or experiment answers

If only filenames or folder placement changed without adding new content, note that config changes may be unnecessary.

## Refresh Rules

Recommend these actions after intake:

- Cloud lightweight app: refresh or redeploy if new source files are added to the repository used by the app.
- Local Chroma app: rebuild the vector index if new source files are added or document contents materially changed.
- Config-only changes: reload or restart the app and rebuild the index if routing or corpus selection depends on the vector store.

## When To Escalate

Pause and ask the user before proceeding if:

- the material appears copyrighted or source-unclear for public upload
- OCR is required but no OCR path is available
- a scanned PDF is the only copy and quality is too poor for reliable extraction
- the correct topic group is ambiguous across two or more core groups

## Scripts

Use these scripts as the default workflow:

- `scripts/scan_materials_intake.py`: scan a folder of new materials and emit an intake report.
- `scripts/export_ppt_to_pdf.ps1`: batch export PowerPoint files to PDF.
- `scripts/intake_to_retrieval_candidates.py`: convert intake results into retrieval-config candidate entries.
- `scripts/run_ocr_queue.py`: build a queued OCR plan from `needs_ocr` records and optionally execute `ocrmypdf` when OCR tools are installed.

Examples:

```bash
python skills/biomedical-teaching-materials-intake/scripts/scan_materials_intake.py materials/course-slides --json-output tmp/intake.json --md-output tmp/intake.md
```

```bash
python skills/biomedical-teaching-materials-intake/scripts/run_ocr_queue.py tmp/intake.json --source-root materials/course-slides --output-dir materials/course-slides-ocr --json-output tmp/ocr-queue.json --md-output tmp/ocr-queue.md
```

## References

Read [intake-checklist.md](references/intake-checklist.md) for the intake decision checklist.
Read [routing-rules.md](references/routing-rules.md) for naming, folder placement, and source-group routing guidance.
Read [ocr-workflow.md](references/ocr-workflow.md) for OCR execution and post-OCR verification.

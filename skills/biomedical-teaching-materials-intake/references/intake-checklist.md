# Intake Checklist

## 1. File Type Check

For each new file, identify the actual working type:

- `pdf`: preferred if text is selectable
- `md`, `txt`, `html`: directly usable in most cases
- `pptx`, `docx`: convert to PDF before intake
- image-only assets: not retrieval-ready unless OCR or supporting text exists

## 2. PDF Readiness Check

If the file is a PDF, decide one of four outcomes:

- eady_pdf: text-selectable and extractable
- eady_text_source: markdown, text, or html source that can be indexed directly
- 
eeds_ocr: scanned pages, screenshots, or image-only pages dominate
- convert_to_pdf: not a PDF yet but should become one
- 
ot_recommended: poor quality, duplicate, or legally risky

Signals that a PDF likely needs OCR:

- copy-paste text fails or returns almost nothing
- pages visually look like scanned slides or photographed documents
- extracted text is fragmented, garbled, or missing headings
- every page behaves like one large image

## 3. Teaching Value Check

Prioritize files that are:

- written by the course teacher
- aligned to the current semester's syllabus
- explicit about methods, steps, and terminology
- better than existing public fallback sources

Lower priority or reject files that are:

- duplicated with newer course versions available
- generic and weaker than existing course-authored files
- source-unclear or risky to redistribute publicly

## 4. Output Template

For each file, report:

- `file`
- `format`
- `intake_state`
- `recommended_folder`
- `normalized_name`
- `source_group`
- `config_update`
- `refresh_action`
- `notes`

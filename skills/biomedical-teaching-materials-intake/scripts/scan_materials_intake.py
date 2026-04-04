from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

TEXT_EXTENSIONS = {'.md', '.txt', '.html', '.htm'}
CONVERT_TO_PDF_EXTENSIONS = {'.ppt', '.pptx', '.doc', '.docx'}
SKIP_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff', '.zip', '.rar'}

TOPIC_PATTERNS = [
    ('hdsemg_core', ['hdsemg', 'high-density emg', 'high density emg']),
    ('ecg_core', ['ecg', 'qrs', 'hrv', 'electrocard']),
    ('emg_core', ['emg', 'electromyography', 'surface electromyography', 'sEMG']),
    ('eeg_core', ['eeg', 'erp', 'electroenceph']),
    ('ppg_core', ['ppg', 'photopleth']),
    ('fnirs_core', ['fnirs', 'nirs', 'optical density', 'hemodynamic']),
    ('theory_core', ['sampling', 'filter', 'fft', 'stft', 'wavelet', 'signal processing', 'preprocessing']),
]

LAB_HINTS = ['lab', 'experiment', '实验', 'labguide']
ASSIGNMENT_HINTS = ['assignment', 'homework', '作业', 'rubric', 'faq']


@dataclass
class IntakeRecord:
    file: str
    relative_path: str
    format: str
    intake_state: str
    recommended_folder: str
    normalized_name: str
    source_group: str
    config_update: bool
    refresh_action: str
    notes: str
    pages_scanned: int | None = None
    extracted_characters: int | None = None
    text_pages: int | None = None


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob('*')):
        if path.is_file():
            yield path


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text or 'untitled'


def choose_topic_group(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ASSIGNMENT_HINTS):
        return 'assignment_support'
    if any(token in lowered for token in LAB_HINTS):
        return 'lab_core'
    for group, patterns in TOPIC_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return group
    return 'theory_core'


def choose_folder(source_group: str) -> str:
    if source_group == 'assignment_support':
        return 'materials/assignments/'
    if source_group == 'lab_core':
        return 'materials/lab-guides/'
    return 'materials/course-slides/'


def normalize_name(path: Path, source_group: str) -> str:
    stem = slugify(path.stem)
    suffix = path.suffix.lower() or '.pdf'
    prefix = 'course'
    if source_group == 'lab_core':
        prefix = 'lab'
    elif source_group == 'assignment_support':
        prefix = 'assignment'
    return f'{prefix}_{stem}{suffix}'


def classify_pdf(path: Path, max_pages: int) -> tuple[str, str, int, int, int]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        return 'needs_ocr', f'PDF could not be parsed reliably: {exc}', 0, 0, 0

    page_count = min(len(reader.pages), max_pages)
    extracted_characters = 0
    text_pages = 0

    for index in range(page_count):
        try:
            text = reader.pages[index].extract_text() or ''
        except Exception:
            text = ''
        compact = ''.join(text.split())
        extracted_characters += len(compact)
        if len(compact) >= 80:
            text_pages += 1

    if page_count == 0:
        return 'not_recommended', 'PDF has no readable pages.', page_count, extracted_characters, text_pages

    text_ratio = text_pages / page_count if page_count else 0.0
    avg_chars = extracted_characters / page_count if page_count else 0.0

    if extracted_characters < 120 or text_ratio < 0.35 or avg_chars < 40:
        return 'needs_ocr', 'Likely scanned or image-dominant PDF. Run OCR before intake.', page_count, extracted_characters, text_pages

    if extracted_characters < 500:
        return 'ready_pdf', 'PDF is readable but text density is low. Verify key headings after intake.', page_count, extracted_characters, text_pages

    return 'ready_pdf', 'PDF contains extractable text and is ready for intake.', page_count, extracted_characters, text_pages


def classify_file(path: Path, root: Path, max_pdf_pages: int) -> IntakeRecord:
    suffix = path.suffix.lower()
    name_context = f'{path.name} {path.parent.name}'
    source_group = choose_topic_group(name_context)
    recommended_folder = choose_folder(source_group)
    normalized_name = normalize_name(path, source_group)
    refresh_action = 'rebuild_index_and_redeploy_cloud'
    config_update = source_group != 'theory_core' or 'lab' in recommended_folder or 'assignment' in recommended_folder
    pages_scanned = None
    extracted_characters = None
    text_pages = None

    if suffix == '.pdf':
        intake_state, notes, pages_scanned, extracted_characters, text_pages = classify_pdf(path, max_pdf_pages)
    elif suffix in TEXT_EXTENSIONS:
        intake_state = 'ready_text_source'
        notes = 'Directly usable text-based source.'
        refresh_action = 'rebuild_index_and_refresh_cloud'
    elif suffix in CONVERT_TO_PDF_EXTENSIONS:
        intake_state = 'convert_to_pdf'
        notes = 'Convert or export to PDF before intake for stable retrieval.'
        refresh_action = 'convert_then_rebuild_index'
    elif suffix in SKIP_EXTENSIONS:
        intake_state = 'not_recommended'
        notes = 'Binary asset or image file. Add supporting OCR/text source before intake.'
        refresh_action = 'no_refresh_needed'
        config_update = False
    else:
        intake_state = 'not_recommended'
        notes = 'Unsupported or unclear format for knowledge-base retrieval.'
        refresh_action = 'no_refresh_needed'
        config_update = False

    return IntakeRecord(
        file=path.name,
        relative_path=path.relative_to(root).as_posix(),
        format=suffix.lstrip('.') or 'unknown',
        intake_state=intake_state,
        recommended_folder=recommended_folder,
        normalized_name=normalized_name,
        source_group=source_group,
        config_update=config_update,
        refresh_action=refresh_action,
        notes=notes,
        pages_scanned=pages_scanned,
        extracted_characters=extracted_characters,
        text_pages=text_pages,
    )


def render_markdown(records: list[IntakeRecord], root: Path) -> str:
    lines = [
        f'# Materials Intake Report',
        '',
        f'- Root: `{root}`',
        f'- Files scanned: `{len(records)}`',
        '',
        '| File | Format | State | Source Group | Recommended Folder | Refresh | Notes |',
        '|---|---|---|---|---|---|---|',
    ]
    for record in records:
        lines.append(
            f"| `{record.relative_path}` | `{record.format}` | `{record.intake_state}` | `{record.source_group}` | `{record.recommended_folder}` | `{record.refresh_action}` | {record.notes} |"
        )
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Scan teaching materials and generate an intake report.')
    parser.add_argument('input_dir', help='Directory containing new materials to scan.')
    parser.add_argument('--json-output', help='Optional path for JSON output.')
    parser.add_argument('--md-output', help='Optional path for Markdown output.')
    parser.add_argument('--max-pdf-pages', type=int, default=6, help='Maximum number of PDF pages to inspect.')
    args = parser.parse_args()

    root = Path(args.input_dir).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f'Input directory not found: {root}')

    records = [classify_file(path, root, args.max_pdf_pages) for path in iter_files(root)]

    if args.json_output:
        json_path = Path(args.json_output).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps([asdict(item) for item in records], ensure_ascii=False, indent=2), encoding='utf-8')

    if args.md_output:
        md_path = Path(args.md_output).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(records, root), encoding='utf-8')

    print(json.dumps([asdict(item) for item in records], ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

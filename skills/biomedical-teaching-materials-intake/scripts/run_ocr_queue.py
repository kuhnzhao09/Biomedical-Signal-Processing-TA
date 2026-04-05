from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

NEEDS_OCR_STATE = 'needs_ocr'
P1_TERMS = [
    'adaptive',
    'wiener',
    'qrs',
    'ecg',
    '\u81ea\u9002\u5e94',
    '\u7ef4\u7eb3',
    '\u6ee4\u6ce2',
]
P2_TERMS = [
    'random',
    'correlation',
    'stochastic',
    '\u968f\u673a',
    '\u76f8\u5173',
]
GROUP_BASE_PRIORITY = {
    'lab_core': 'P1',
    'ecg_core': 'P1',
    'emg_core': 'P1',
    'hdsemg_core': 'P1',
    'eeg_core': 'P1',
    'ppg_core': 'P1',
    'fnirs_core': 'P1',
    'assignment_support': 'P2',
    'theory_core': 'P2',
}
PRIORITY_ORDER = {'P1': 1, 'P2': 2, 'P3': 3}
KNOWN_PRIORITY_OVERRIDES = {
    'course_5_2.pdf': ('P1', 'Known method-core Wiener-Hopf lecture from the Raonini batch.'),
    'course_8_1.pdf': ('P1', 'Known method-core adaptive-filtering fundamentals lecture from the Raonini batch.'),
    'course_8_2.pdf': ('P1', 'Known adaptive noise-cancellation lecture from the Raonini batch.'),
    'course_3_1.pdf': ('P2', 'Known supporting-theory random-signal lecture from the Raonini batch.'),
    'course_4_2.pdf': ('P2', 'Known supporting-theory correlation lecture from the Raonini batch.'),
    'course_8_4.pdf': ('P3', 'Known application-focused adaptive-filtering lecture from the Raonini batch.'),
}


@dataclass
class OCRTask:
    priority: str
    file: str
    relative_path: str
    normalized_name: str
    source_group: str
    pages_scanned: int | None
    extracted_characters: int | None
    text_pages: int | None
    input_pdf: str
    output_pdf: str
    priority_reason: str
    suggested_command: str


def normalize_path(path: Path | str) -> str:
    return str(path).replace('\\', '/')


def load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, list):
        raise SystemExit('Expected intake JSON to contain a list of records.')
    return payload


def choose_priority(record: dict[str, Any]) -> tuple[str, str]:
    name = f"{record.get('file', '')} {record.get('normalized_name', '')}".lower()
    source_group = record.get('source_group', 'theory_core')
    text_pages = int(record.get('text_pages') or 0)
    normalized_name = record.get('normalized_name', '')

    if normalized_name in KNOWN_PRIORITY_OVERRIDES:
        priority, reason = KNOWN_PRIORITY_OVERRIDES[normalized_name]
        return priority, reason

    if any(term in name for term in P1_TERMS):
        return 'P1', 'Matched high-value OCR keywords in the file name.'
    if source_group in GROUP_BASE_PRIORITY and GROUP_BASE_PRIORITY[source_group] == 'P1':
        return 'P1', f'Source group `{source_group}` is treated as first-line teaching material.'
    if text_pages == 0:
        return 'P1', 'PDF appears fully image-based and should be OCRed before later batches.'
    if any(term in name for term in P2_TERMS):
        return 'P2', 'Matched supporting-theory OCR keywords in the file name.'
    return GROUP_BASE_PRIORITY.get(source_group, 'P3'), f'Defaulted from source group `{source_group}`.'


def make_command(ocrmypdf_path: str, language: str, input_pdf: Path, output_pdf: Path) -> list[str]:
    command = [
        ocrmypdf_path,
        '--skip-text',
        '--rotate-pages',
        '--deskew',
        '--force-ocr',
    ]
    if language:
        command.extend(['--language', language])
    command.extend([str(input_pdf), str(output_pdf)])
    return command


def build_tasks(records: list[dict[str, Any]], source_root: Path, output_root: Path, language: str) -> list[OCRTask]:
    ocrmypdf_path = shutil.which('ocrmypdf') or 'ocrmypdf'
    tasks: list[OCRTask] = []

    for item in records:
        if item.get('intake_state') != NEEDS_OCR_STATE:
            continue
        relative_path = item.get('relative_path', '')
        if not relative_path:
            continue
        input_pdf = (source_root / relative_path).resolve()
        output_pdf = (output_root / relative_path).resolve()
        priority, reason = choose_priority(item)
        command = make_command(ocrmypdf_path, language, input_pdf, output_pdf)
        tasks.append(
            OCRTask(
                priority=priority,
                file=item.get('file', input_pdf.name),
                relative_path=relative_path,
                normalized_name=item.get('normalized_name', ''),
                source_group=item.get('source_group', 'theory_core'),
                pages_scanned=item.get('pages_scanned'),
                extracted_characters=item.get('extracted_characters'),
                text_pages=item.get('text_pages'),
                input_pdf=normalize_path(input_pdf),
                output_pdf=normalize_path(output_pdf),
                priority_reason=reason,
                suggested_command=subprocess.list2cmdline(command),
            )
        )

    tasks.sort(key=lambda task: (PRIORITY_ORDER.get(task.priority, 9), task.file))
    return tasks


def render_markdown(tasks: list[OCRTask], source_root: Path, output_root: Path, language: str, execute: bool, tools_ready: bool) -> str:
    lines = [
        '# OCR Queue',
        '',
        f'- Source root: `{normalize_path(source_root)}`',
        f'- Output root: `{normalize_path(output_root)}`',
        f'- Files queued: `{len(tasks)}`',
        f'- OCR language: `{language or "default"}`',
        f'- Execution requested: `{str(execute).lower()}`',
        f'- OCR tools ready: `{str(tools_ready).lower()}`',
        '',
        '| Priority | File | Source Group | OCR Signal | Output | Reason |',
        '|---|---|---|---|---|---|',
    ]
    for task in tasks:
        signal = f"{task.pages_scanned} pages, {task.extracted_characters} chars, {task.text_pages} text pages"
        lines.append(
            f"| `{task.priority}` | `{task.file}` | `{task.source_group}` | `{signal}` | `{task.output_pdf}` | {task.priority_reason} |"
        )
    lines.append('')
    return '\n'.join(lines)


def run_tasks(tasks: list[OCRTask], language: str) -> list[dict[str, Any]]:
    ocrmypdf_path = shutil.which('ocrmypdf')
    if not ocrmypdf_path:
        raise SystemExit('ocrmypdf is not installed or not on PATH. Install OCRmyPDF and Tesseract first, or rerun without --execute.')

    results: list[dict[str, Any]] = []
    for task in tasks:
        output_path = Path(task.output_pdf)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = make_command(ocrmypdf_path, language, Path(task.input_pdf), output_path)
        completed = subprocess.run(command, capture_output=True, text=True)
        results.append(
            {
                'file': task.file,
                'priority': task.priority,
                'returncode': completed.returncode,
                'stdout_tail': completed.stdout[-2000:],
                'stderr_tail': completed.stderr[-2000:],
                'output_pdf': task.output_pdf,
            }
        )
        if completed.returncode != 0:
            break
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description='Build and optionally execute an OCR queue from a materials intake report.')
    parser.add_argument('intake_json', help='Path to intake JSON produced by scan_materials_intake.py')
    parser.add_argument('--source-root', required=True, help='Original directory that was scanned to create the intake report.')
    parser.add_argument('--output-dir', required=True, help='Directory for OCR output PDFs.')
    parser.add_argument('--language', default='chi_sim+eng', help='OCR language hint passed to OCRmyPDF.')
    parser.add_argument('--json-output', help='Optional path for queue JSON output.')
    parser.add_argument('--md-output', help='Optional path for queue Markdown output.')
    parser.add_argument('--execute', action='store_true', help='Actually run OCRmyPDF on queued files.')
    args = parser.parse_args()

    intake_path = Path(args.intake_json).resolve()
    source_root = Path(args.source_root).resolve()
    output_root = Path(args.output_dir).resolve()
    if not intake_path.exists():
        raise SystemExit(f'Intake JSON not found: {intake_path}')
    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(f'Source root not found: {source_root}')

    records = load_records(intake_path)
    tasks = build_tasks(records, source_root, output_root, args.language)
    payload: dict[str, Any] = {
        'version': 1,
        'intake_json': normalize_path(intake_path),
        'source_root': normalize_path(source_root),
        'output_root': normalize_path(output_root),
        'ocr_language': args.language,
        'execute_requested': args.execute,
        'ocrmypdf_available': shutil.which('ocrmypdf') is not None,
        'tesseract_available': shutil.which('tesseract') is not None,
        'tasks': [asdict(task) for task in tasks],
    }

    if args.execute:
        payload['execution_results'] = run_tasks(tasks, args.language)

    if args.json_output:
        json_path = Path(args.json_output).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.md_output:
        md_path = Path(args.md_output).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(
            render_markdown(
                tasks,
                source_root,
                output_root,
                args.language,
                args.execute,
                payload['ocrmypdf_available'] and payload['tesseract_available'],
            ),
            encoding='utf-8',
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

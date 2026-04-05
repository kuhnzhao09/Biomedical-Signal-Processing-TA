from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

NEEDS_OCR_STATE = 'needs_ocr'
P1_TERMS = [
    'adaptive',
    'wiener',
    'qrs',
    'ecg',
    '???',
    '??',
    '??',
]
P2_TERMS = [
    'random',
    'correlation',
    'stochastic',
    '??',
    '??',
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


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def runtime_tmp_dir() -> Path:
    base = Path.home() / 'bsp_ocr_tmp'
    path = base / f'run-{uuid.uuid4().hex}'
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_executable(name: str, extra_candidates: list[Path]) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for candidate in extra_candidates:
        if candidate.exists():
            return str(candidate)
    return None


def resolve_toolchain() -> dict[str, str | None]:
    root = workspace_root()
    user_scripts = Path.home() / 'AppData' / 'Roaming' / 'Python' / 'Python312' / 'Scripts'
    tesseract_dir = Path(r'C:/Program Files/Tesseract-OCR')
    ghostscript_candidates = sorted(Path(r'D:/Program Files/gs').glob('gs*/bin/gswin64c.exe'), reverse=True)
    if not ghostscript_candidates:
        ghostscript_candidates = sorted(Path(r'C:/Program Files/gs').glob('gs*/bin/gswin64c.exe'), reverse=True)

    ocrmypdf_path = resolve_executable('ocrmypdf', [user_scripts / 'ocrmypdf.exe'])
    tesseract_path = resolve_executable('tesseract', [tesseract_dir / 'tesseract.exe'])
    gswin64c_path = resolve_executable('gswin64c', ghostscript_candidates)

    tessdata_root = root / 'tools'
    tessdata_dir = tessdata_root / 'tessdata'
    if not tessdata_dir.exists():
        tessdata_root = None

    return {
        'ocrmypdf': ocrmypdf_path,
        'tesseract': tesseract_path,
        'gswin64c': gswin64c_path,
        'user_scripts': str(user_scripts) if user_scripts.exists() else None,
        'tesseract_dir': str(tesseract_dir) if tesseract_dir.exists() else None,
        'ghostscript_bin': str(Path(gswin64c_path).parent) if gswin64c_path else None,
        'tessdata_prefix': str(tessdata_dir) if tessdata_root else None,
    }


def build_runtime_env(toolchain: dict[str, str | None]) -> dict[str, str]:
    env = os.environ.copy()
    path_parts = [env.get('PATH', '')]
    for key in ('user_scripts', 'tesseract_dir', 'ghostscript_bin'):
        value = toolchain.get(key)
        if value:
            path_parts.insert(0, value)
    env['PATH'] = os.pathsep.join(part for part in path_parts if part)
    if toolchain.get('tessdata_prefix'):
        env['TESSDATA_PREFIX'] = toolchain['tessdata_prefix']
    tmp_dir = runtime_tmp_dir()
    env['TMP'] = str(tmp_dir)
    env['TEMP'] = str(tmp_dir)
    return env


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
        return KNOWN_PRIORITY_OVERRIDES[normalized_name]
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
        '--rotate-pages',
        '--deskew',
        '--force-ocr',
        '--jobs',
        '1',
    ]
    if language:
        command.extend(['--language', language])
    command.extend([str(input_pdf), str(output_pdf)])
    return command


def build_tasks(records: list[dict[str, Any]], source_root: Path, output_root: Path, language: str, ocrmypdf_path: str) -> list[OCRTask]:
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


def render_markdown(tasks: list[OCRTask], source_root: Path, output_root: Path, language: str, execute: bool, toolchain: dict[str, str | None]) -> str:
    tools_ready = bool(toolchain.get('ocrmypdf') and toolchain.get('tesseract') and toolchain.get('gswin64c'))
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
        lines.append(f"| `{task.priority}` | `{task.file}` | `{task.source_group}` | `{signal}` | `{task.output_pdf}` | {task.priority_reason} |")
    lines.extend([
        '',
        '## Toolchain',
        '',
        f"- ocrmypdf: `{toolchain.get('ocrmypdf') or 'NOT_FOUND'}`",
        f"- tesseract: `{toolchain.get('tesseract') or 'NOT_FOUND'}`",
        f"- gswin64c: `{toolchain.get('gswin64c') or 'NOT_FOUND'}`",
        f"- TESSDATA_PREFIX: `{toolchain.get('tessdata_prefix') or 'default'}`",
        '',
    ])
    return '\n'.join(lines)


def run_tasks(tasks: list[OCRTask], language: str, toolchain: dict[str, str | None]) -> list[dict[str, Any]]:
    ocrmypdf_path = toolchain.get('ocrmypdf')
    tesseract_path = toolchain.get('tesseract')
    gswin64c_path = toolchain.get('gswin64c')
    if not ocrmypdf_path or not tesseract_path or not gswin64c_path:
        raise SystemExit('OCR toolchain is incomplete. Ensure OCRmyPDF, Tesseract, and Ghostscript are installed or discoverable.')

    env = build_runtime_env(toolchain)
    results: list[dict[str, Any]] = []
    for task in tasks:
        output_path = Path(task.output_pdf)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and output_path.stat().st_size > 0:
            results.append({
                'file': task.file,
                'priority': task.priority,
                'returncode': 0,
                'skipped_existing': True,
                'stdout_tail': '',
                'stderr_tail': 'Skipped because OCR output already exists.',
                'output_pdf': task.output_pdf,
            })
            continue
        command = make_command(ocrmypdf_path, language, Path(task.input_pdf), output_path)
        completed = subprocess.run(command, capture_output=True, text=True, env=env)
        results.append(
            {
                'file': task.file,
                'priority': task.priority,
                'returncode': completed.returncode,
                'stdout_tail': completed.stdout[-4000:],
                'stderr_tail': completed.stderr[-4000:],
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

    toolchain = resolve_toolchain()
    ocrmypdf_path = toolchain.get('ocrmypdf') or 'ocrmypdf'
    records = load_records(intake_path)
    tasks = build_tasks(records, source_root, output_root, args.language, ocrmypdf_path)
    payload: dict[str, Any] = {
        'version': 1,
        'intake_json': normalize_path(intake_path),
        'source_root': normalize_path(source_root),
        'output_root': normalize_path(output_root),
        'ocr_language': args.language,
        'execute_requested': args.execute,
        'ocrmypdf_available': toolchain.get('ocrmypdf') is not None,
        'tesseract_available': toolchain.get('tesseract') is not None,
        'ghostscript_available': toolchain.get('gswin64c') is not None,
        'toolchain': toolchain,
        'tasks': [asdict(task) for task in tasks],
    }

    if args.execute:
        payload['execution_results'] = run_tasks(tasks, args.language, toolchain)

    if args.json_output:
        json_path = Path(args.json_output).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.md_output:
        md_path = Path(args.md_output).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(tasks, source_root, output_root, args.language, args.execute, toolchain), encoding='utf-8')

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any

import yaml

READY_STATES = {'ready_pdf', 'ready_text_source'}


def normalize_path(path: Path | str) -> str:
    return str(path).replace('\\', '/')


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f'Could not load module: {module_path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def sync_config_files(config: dict[str, Any], json_path: Path, yaml_path: Path | None, py_path: Path | None) -> None:
    write_json(json_path, config)
    if yaml_path is not None:
        write_text(yaml_path, yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    if py_path is not None:
        write_text(py_path, 'CONFIG = ' + pformat(config, sort_dicts=False, width=100) + '\n')


def rescan_directory(scan_module: Any, root: Path, max_pdf_pages: int) -> list[dict[str, Any]]:
    records = [scan_module.classify_file(path, root, max_pdf_pages) for path in scan_module.iter_files(root)]
    return [asdict(item) for item in records]


def build_promoted_records(original_records: list[dict[str, Any]], rescanned_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    original_needs = {
        item.get('relative_path'): item
        for item in original_records
        if item.get('intake_state') == 'needs_ocr' and item.get('relative_path')
    }

    promoted: list[dict[str, Any]] = []
    still_blocked: list[dict[str, Any]] = []
    for item in rescanned_records:
        rel_path = item.get('relative_path')
        if rel_path not in original_needs:
            continue
        if item.get('intake_state') in READY_STATES:
            promoted.append(item)
        else:
            still_blocked.append(item)

    promoted.sort(key=lambda x: (x.get('source_group', ''), x.get('relative_path', '')))
    still_blocked.sort(key=lambda x: x.get('relative_path', ''))
    return promoted, still_blocked


def merge_candidates_into_config(config: dict[str, Any], candidate_payload: dict[str, Any]) -> dict[str, Any]:
    source_groups = config.setdefault('source_groups', {})
    summary = {
        'appended_paths': {},
        'created_groups': {},
        'deduped_existing_paths': {},
    }

    for group, paths in candidate_payload.get('append_to_existing_groups', {}).items():
        group_entry = source_groups.setdefault(group, {'priority': 2, 'weight': 0.9, 'paths': []})
        existing_paths = list(group_entry.get('paths', []))
        seen = set(existing_paths)
        appended: list[str] = []
        skipped: list[str] = []
        for path in paths:
            if path in seen:
                skipped.append(path)
                continue
            existing_paths.append(path)
            seen.add(path)
            appended.append(path)
        group_entry['paths'] = existing_paths
        summary['appended_paths'][group] = appended
        summary['deduped_existing_paths'][group] = skipped

    for group, group_payload in candidate_payload.get('create_new_source_groups', {}).items():
        if group in source_groups:
            existing_paths = list(source_groups[group].get('paths', []))
            seen = set(existing_paths)
            appended: list[str] = []
            skipped: list[str] = []
            for path in group_payload.get('paths', []):
                if path in seen:
                    skipped.append(path)
                    continue
                existing_paths.append(path)
                seen.add(path)
                appended.append(path)
            source_groups[group]['paths'] = existing_paths
            summary['appended_paths'][group] = appended
            summary['deduped_existing_paths'][group] = skipped
            continue

        source_groups[group] = {
            'priority': group_payload.get('priority', 2),
            'weight': group_payload.get('weight', 0.9),
            'paths': list(group_payload.get('paths', [])),
        }
        summary['created_groups'][group] = source_groups[group]
        summary['appended_paths'][group] = list(group_payload.get('paths', []))
        summary['deduped_existing_paths'][group] = []

    return summary


def render_merge_report(
    ocr_root: Path,
    rescanned_records: list[dict[str, Any]],
    promoted_records: list[dict[str, Any]],
    still_blocked: list[dict[str, Any]],
    merge_summary: dict[str, Any],
    candidate_payload: dict[str, Any],
) -> str:
    lines = [
        '# Post-OCR Intake Merge Report',
        '',
        f'- OCR root: `{normalize_path(ocr_root)}`',
        f'- Rescanned files: `{len(rescanned_records)}`',
        f'- Promoted from `needs_ocr` to ready: `{len(promoted_records)}`',
        f'- Still blocked after OCR scan: `{len(still_blocked)}`',
        f'- Report generated: `{datetime.now().isoformat(timespec="seconds")}`',
        '',
        '## Promoted Files',
        '',
    ]

    if not promoted_records:
        lines.append('(none)')
        lines.append('')
    else:
        lines.append('| File | State | Source Group | Relative Path |')
        lines.append('|---|---|---|---|')
        for item in promoted_records:
            lines.append(
                f"| `{item.get('file', '')}` | `{item.get('intake_state', '')}` | `{item.get('source_group', '')}` | `{item.get('relative_path', '')}` |"
            )
        lines.append('')

    lines.append('## Merge Summary')
    lines.append('')
    appended_any = False
    for group, paths in merge_summary.get('appended_paths', {}).items():
        if not paths:
            continue
        appended_any = True
        lines.append(f'### {group}')
        lines.append('')
        for path in paths:
            lines.append(f'- appended: `{path}`')
        lines.append('')
    if not appended_any:
        lines.append('(no new paths appended)')
        lines.append('')

    created_groups = merge_summary.get('created_groups', {})
    lines.append('## Created Groups')
    lines.append('')
    if not created_groups:
        lines.append('(none)')
    else:
        for group, payload in created_groups.items():
            lines.append(f'- `{group}` with `{len(payload.get("paths", []))}` path(s)')
    lines.append('')

    lines.append('## Still Blocked')
    lines.append('')
    if not still_blocked:
        lines.append('(none)')
    else:
        lines.append('| File | State | Notes |')
        lines.append('|---|---|---|')
        for item in still_blocked:
            lines.append(
                f"| `{item.get('file', '')}` | `{item.get('intake_state', '')}` | {item.get('notes', '')} |"
            )
    lines.append('')

    lines.append('## Candidate Payload Summary')
    lines.append('')
    lines.append(f"- append groups: `{len(candidate_payload.get('append_to_existing_groups', {}))}`")
    lines.append(f"- create groups: `{len(candidate_payload.get('create_new_source_groups', {}))}`")
    lines.append(f"- skipped records: `{len(candidate_payload.get('skipped', []))}`")
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='After OCR is complete, rescan OCR outputs and merge promoted files into retrieval config.')
    parser.add_argument('ocr_dir', help='Directory containing OCR output PDFs.')
    parser.add_argument('--original-intake-json', required=True, help='Original intake JSON containing `needs_ocr` records.')
    parser.add_argument('--retrieval-config-json', required=True, help='Main retrieval config JSON to update.')
    parser.add_argument('--retrieval-config-yaml', help='Optional YAML config to sync.')
    parser.add_argument('--retrieval-config-py', help='Optional Python config to sync.')
    parser.add_argument('--rescanned-json-output', help='Optional path for the OCR-output rescan JSON.')
    parser.add_argument('--rescanned-md-output', help='Optional path for the OCR-output rescan Markdown report.')
    parser.add_argument('--candidate-json-output', help='Optional path for promoted-candidate JSON.')
    parser.add_argument('--candidate-md-output', help='Optional path for promoted-candidate Markdown summary.')
    parser.add_argument('--merge-report-md-output', help='Optional path for a merge report.')
    parser.add_argument('--max-pdf-pages', type=int, default=6, help='Maximum number of PDF pages to inspect during post-OCR rescan.')
    args = parser.parse_args()

    root = Path(args.ocr_dir).resolve()
    original_intake_json = Path(args.original_intake_json).resolve()
    retrieval_json = Path(args.retrieval_config_json).resolve()
    retrieval_yaml = Path(args.retrieval_config_yaml).resolve() if args.retrieval_config_yaml else None
    retrieval_py = Path(args.retrieval_config_py).resolve() if args.retrieval_config_py else None

    if not root.exists() or not root.is_dir():
        raise SystemExit(f'OCR directory not found: {root}')
    if not original_intake_json.exists():
        raise SystemExit(f'Original intake JSON not found: {original_intake_json}')
    if not retrieval_json.exists():
        raise SystemExit(f'Retrieval config JSON not found: {retrieval_json}')
    if retrieval_yaml is not None and not retrieval_yaml.exists():
        raise SystemExit(f'Retrieval config YAML not found: {retrieval_yaml}')
    if retrieval_py is not None and not retrieval_py.exists():
        raise SystemExit(f'Retrieval config Python file not found: {retrieval_py}')

    scripts_dir = Path(__file__).resolve().parent
    scan_module = load_module(scripts_dir / 'scan_materials_intake.py', 'scan_materials_intake_mod')
    candidate_module = load_module(scripts_dir / 'intake_to_retrieval_candidates.py', 'intake_to_candidates_mod')

    original_records = load_json(original_intake_json)
    if not isinstance(original_records, list):
        raise SystemExit('Expected original intake JSON to contain a list of records.')

    rescanned_records = rescan_directory(scan_module, root, args.max_pdf_pages)
    promoted_records, still_blocked = build_promoted_records(original_records, rescanned_records)
    known_groups = candidate_module.load_known_groups(retrieval_json)
    candidate_payload = candidate_module.build_append_candidates(promoted_records, root, known_groups)

    config = load_json(retrieval_json)
    if not isinstance(config, dict):
        raise SystemExit('Expected retrieval config JSON to contain a mapping.')
    merge_summary = merge_candidates_into_config(config, candidate_payload)
    has_merge_changes = any(merge_summary.get('appended_paths', {}).get(group) for group in merge_summary.get('appended_paths', {})) or bool(merge_summary.get('created_groups'))
    if has_merge_changes:
        sync_config_files(config, retrieval_json, retrieval_yaml, retrieval_py)

    if args.rescanned_json_output:
        write_json(Path(args.rescanned_json_output).resolve(), rescanned_records)
    if args.rescanned_md_output:
        write_text(Path(args.rescanned_md_output).resolve(), scan_module.render_markdown([scan_module.IntakeRecord(**item) for item in rescanned_records], root))
    if args.candidate_json_output:
        write_json(Path(args.candidate_json_output).resolve(), candidate_payload)
    if args.candidate_md_output:
        write_text(Path(args.candidate_md_output).resolve(), candidate_module.render_markdown(candidate_payload))
    if args.merge_report_md_output:
        write_text(
            Path(args.merge_report_md_output).resolve(),
            render_merge_report(root, rescanned_records, promoted_records, still_blocked, merge_summary, candidate_payload),
        )

    result = {
        'ocr_root': normalize_path(root),
        'rescanned_files': len(rescanned_records),
        'promoted_files': len(promoted_records),
        'still_blocked_files': len(still_blocked),
        'appended_paths': merge_summary.get('appended_paths', {}),
        'created_groups': merge_summary.get('created_groups', {}),
        'config_updated': has_merge_changes,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

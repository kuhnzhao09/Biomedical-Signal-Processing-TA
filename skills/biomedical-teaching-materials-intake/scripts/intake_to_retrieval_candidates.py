from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

READY_STATES = {'ready_pdf', 'ready_text_source'}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def load_known_groups(config_path: Path | None) -> set[str]:
    if config_path is None:
        return set()
    payload = load_json(config_path)
    if not isinstance(payload, dict):
        return set()
    groups = payload.get('source_groups', {})
    if not isinstance(groups, dict):
        return set()
    return set(groups.keys())


def build_append_candidates(
    intake_records: list[dict[str, Any]],
    source_root: Path,
    known_groups: set[str],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    skipped: list[dict[str, Any]] = []

    for item in intake_records:
        state = item.get('intake_state', '')
        rel_path = item.get('relative_path', '')
        group = item.get('source_group', '')
        notes = item.get('notes', '')
        absolute_path = str((source_root / rel_path).resolve()).replace('\\', '/') if rel_path else ''

        candidate = {
            'path': absolute_path,
            'relative_path': rel_path,
            'source_group': group,
            'normalized_name': item.get('normalized_name', ''),
            'intake_state': state,
            'config_update': bool(item.get('config_update', False)),
            'refresh_action': item.get('refresh_action', ''),
            'notes': notes,
        }

        if state in READY_STATES and group:
            grouped[group].append(candidate)
        else:
            skipped.append(candidate)

    append_to_existing_groups: dict[str, list[str]] = {}
    create_new_source_groups: dict[str, dict[str, Any]] = {}
    detailed_candidates: dict[str, list[dict[str, Any]]] = {}

    for group in sorted(grouped.keys()):
        deduped_paths: list[str] = []
        seen: set[str] = set()
        details: list[dict[str, Any]] = []
        for item in grouped[group]:
            path = item['path']
            if not path or path in seen:
                continue
            seen.add(path)
            deduped_paths.append(path)
            details.append(item)
        if not deduped_paths:
            continue
        detailed_candidates[group] = details
        if group in known_groups:
            append_to_existing_groups[group] = deduped_paths
        else:
            create_new_source_groups[group] = {
                'priority': 2,
                'weight': 0.9,
                'paths': deduped_paths,
            }

    return {
        'version': 1,
        'generated_from': 'materials intake scan',
        'source_root': str(source_root).replace('\\', '/'),
        'known_source_groups': sorted(known_groups),
        'append_to_existing_groups': append_to_existing_groups,
        'create_new_source_groups': create_new_source_groups,
        'detailed_candidates': detailed_candidates,
        'skipped': skipped,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        '# Retrieval Candidate Suggestions',
        '',
        f"- Source root: `{payload['source_root']}`",
        '',
        '## Append To Existing Groups',
        '',
    ]
    append_groups: dict[str, list[str]] = payload.get('append_to_existing_groups', {})
    if not append_groups:
        lines.append('(none)')
    else:
        for group, paths in append_groups.items():
            lines.append(f'### {group}')
            lines.append('')
            for path in paths:
                lines.append(f'- `{path}`')
            lines.append('')

    lines.append('## Create New Source Groups')
    lines.append('')
    new_groups: dict[str, dict[str, Any]] = payload.get('create_new_source_groups', {})
    if not new_groups:
        lines.append('(none)')
    else:
        for group, item in new_groups.items():
            lines.append(f'### {group}')
            lines.append('')
            lines.append(f"- priority: `{item.get('priority')}`")
            lines.append(f"- weight: `{item.get('weight')}`")
            lines.append('- paths:')
            for path in item.get('paths', []):
                lines.append(f'  - `{path}`')
            lines.append('')

    lines.append('## Skipped Or Not Ready')
    lines.append('')
    skipped = payload.get('skipped', [])
    if not skipped:
        lines.append('(none)')
    else:
        lines.append('| Relative Path | State | Source Group | Notes |')
        lines.append('|---|---|---|---|')
        for item in skipped:
            lines.append(
                f"| `{item.get('relative_path', '')}` | `{item.get('intake_state', '')}` | `{item.get('source_group', '')}` | {item.get('notes', '')} |"
            )
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Convert materials intake scan output into retrieval-config candidate entries.')
    parser.add_argument('intake_json', help='Path to intake JSON produced by scan_materials_intake.py')
    parser.add_argument('--source-root', required=True, help='Root directory that was originally scanned.')
    parser.add_argument('--retrieval-config', help='Optional retrieval-priority JSON to detect existing source groups.')
    parser.add_argument('--json-output', help='Optional path for candidate JSON output.')
    parser.add_argument('--md-output', help='Optional path for Markdown summary output.')
    args = parser.parse_args()

    intake_path = Path(args.intake_json).resolve()
    source_root = Path(args.source_root).resolve()
    config_path = Path(args.retrieval_config).resolve() if args.retrieval_config else None

    if not intake_path.exists():
        raise SystemExit(f'Intake JSON not found: {intake_path}')
    if not source_root.exists() or not source_root.is_dir():
        raise SystemExit(f'Source root not found: {source_root}')
    if config_path is not None and not config_path.exists():
        raise SystemExit(f'Retrieval config not found: {config_path}')

    records = load_json(intake_path)
    if not isinstance(records, list):
        raise SystemExit('Expected intake JSON to contain a list of records.')

    known_groups = load_known_groups(config_path)
    payload = build_append_candidates(records, source_root, known_groups)

    if args.json_output:
        json_path = Path(args.json_output).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    if args.md_output:
        md_path = Path(args.md_output).resolve()
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(payload), encoding='utf-8')

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

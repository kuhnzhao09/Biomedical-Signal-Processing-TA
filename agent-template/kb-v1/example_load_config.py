from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
JSON_CONFIG = BASE_DIR / 'retrieval-priority-v1.json'
PY_CONFIG = BASE_DIR / 'retrieval_priority_v1.py'


def load_json_config(path: Path = JSON_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def load_python_config(path: Path = PY_CONFIG) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location('retrieval_priority_v1', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Failed to load config from {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CONFIG


def choose_route(query: str, config: dict[str, Any]) -> str:
    lowered = query.lower()
    query_hints = config.get('routing_hints', {}).get('query_contains', {})
    for needle, route_name in query_hints.items():
        if needle.lower() in lowered:
            return route_name
    return 'concept_general'


def get_route_config(route_name: str, config: dict[str, Any]) -> dict[str, Any]:
    routes = config.get('query_routes', {})
    return routes.get(route_name, routes.get('concept_general', {}))


def resolve_candidate_documents(query: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    route_name = choose_route(query, config)
    route = get_route_config(route_name, config)
    source_groups = config.get('source_groups', {})
    candidates: list[dict[str, Any]] = []

    for group_name in route.get('use', []):
        group = source_groups.get(group_name, {})
        if group.get('exclude_from_default'):
            continue
        for path_str in group.get('paths', []):
            path = Path(path_str)
            candidates.append(
                {
                    'route': route_name,
                    'group': group_name,
                    'priority': group.get('priority', 99),
                    'weight': group.get('weight', 0.0),
                    'path': str(path),
                    'exists': path.exists(),
                }
            )

    candidates.sort(key=lambda item: (item['priority'], -item['weight'], item['path']))
    return candidates


def summarize_for_rag(query: str, config: dict[str, Any], top_n: int = 10) -> dict[str, Any]:
    route_name = choose_route(query, config)
    route = get_route_config(route_name, config)
    candidates = resolve_candidate_documents(query, config)
    return {
        'query': query,
        'route': route_name,
        'answer_policy': route.get('answer_policy', {}),
        'top_k': config.get('retrieval_defaults', {}).get('top_k', 8),
        'candidate_documents': candidates[:top_n],
    }


if __name__ == '__main__':
    config = load_json_config()

    example_queries = [
        'How do I preprocess EEG data in Python?',
        'ECG QRS detection MATLAB homework help',
        'How should I explain fNIRS baseline drift to undergraduates?',
    ]

    for query in example_queries:
        result = summarize_for_rag(query, config, top_n=6)
        print('=' * 80)
        print('QUERY:', result['query'])
        print('ROUTE:', result['route'])
        print('ANSWER_POLICY:', result['answer_policy'] or '{}')
        print('TOP_K:', result['top_k'])
        print('CANDIDATES:')
        for item in result['candidate_documents']:
            print(
                f"  - [{item['group']}] priority={item['priority']} weight={item['weight']:.2f} "
                f"exists={item['exists']} path={item['path']}"
            )

    print('=' * 80)
    print('Tip: pass result[\'candidate_documents\'] into your chunk loader or vector retriever first,')
    print('then apply embedding search or reranking only within those files.')

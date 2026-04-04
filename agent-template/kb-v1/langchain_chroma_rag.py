from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from example_load_config import summarize_for_rag
from local_rag_demo import build_context_block, load_or_build_chunks

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'retrieval-priority-v1.json'
DEFAULT_PERSIST_DIR = BASE_DIR / 'chroma_db'
DEFAULT_COLLECTION = 'biomedical_signal_processing_v1'
DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
ASSIGNMENT_KEYWORDS = ('homework', 'assignment', '作业')


def effective_answer_policy(query: str, summary: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if summary.get('answer_policy'):
        return summary['answer_policy']
    lowered = query.lower()
    if any(keyword.lower() in lowered for keyword in ASSIGNMENT_KEYWORDS):
        return config.get('query_routes', {}).get('assignment_help', {}).get('answer_policy', {})
    return {}

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def import_langchain_runtime() -> tuple[Any, Any, Any]:
    try:
        from langchain_chroma import Chroma
    except ImportError as exc:
        raise RuntimeError(
            'Missing dependency: langchain-chroma. Install the packages listed in requirements-langchain-chroma.txt.'
        ) from exc

    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError('Missing dependency: langchain-core.') from exc

    embeddings_error: Exception | None = None
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return Chroma, Document, HuggingFaceEmbeddings
    except Exception as exc:
        embeddings_error = exc

    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return Chroma, Document, HuggingFaceEmbeddings
    except Exception as exc:
        raise RuntimeError(
            'Missing embedding backend. Install langchain-huggingface or langchain-community plus sentence-transformers.'
        ) from (embeddings_error or exc)


def make_embeddings(model_name: str) -> Any:
    _, _, HuggingFaceEmbeddings = import_langchain_runtime()
    return HuggingFaceEmbeddings(model_name=model_name)


def open_vectorstore(persist_directory: Path, collection_name: str, embedding_model: str) -> Any:
    Chroma, _, _ = import_langchain_runtime()
    embeddings = make_embeddings(embedding_model)
    return Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_directory),
        embedding_function=embeddings,
    )


def all_default_source_items(config: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group_name, group in config.get('source_groups', {}).items():
        if group.get('exclude_from_default'):
            continue
        for path in group.get('paths', []):
            items.append(
                {
                    'path': path,
                    'group': group_name,
                    'priority': group.get('priority', 99),
                    'weight': group.get('weight', 0.0),
                }
            )
    return items


def build_documents(config: dict[str, Any], chunk_size: int, overlap: int) -> list[Any]:
    _, Document, _ = import_langchain_runtime()
    docs: list[Any] = []
    seen_paths: set[str] = set()

    for item in all_default_source_items(config):
        path_str = item['path']
        if path_str in seen_paths:
            continue
        seen_paths.add(path_str)
        path = Path(path_str)
        if not path.exists():
            continue
        chunks = load_or_build_chunks(path, chunk_size=chunk_size, overlap=overlap)
        for idx, chunk in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk,
                    metadata={
                        'source_path': str(path),
                        'source_group': item['group'],
                        'priority': item['priority'],
                        'weight': item['weight'],
                        'chunk_id': idx,
                        'file_name': path.name,
                    },
                )
            )
    return docs


def reset_collection(vectorstore: Any) -> None:
    collection = getattr(vectorstore, '_collection', None)
    if collection is None:
        return
    ids = collection.get(include=[])['ids']
    if ids:
        collection.delete(ids=ids)

def build_index(
    config: dict[str, Any],
    persist_directory: Path,
    collection_name: str,
    embedding_model: str,
    chunk_size: int,
    overlap: int,
    batch_size: int,
    reset: bool,
) -> None:
    persist_directory.mkdir(parents=True, exist_ok=True)
    vectorstore = open_vectorstore(persist_directory, collection_name, embedding_model)
    if reset:
        reset_collection(vectorstore)

    docs = build_documents(config, chunk_size=chunk_size, overlap=overlap)
    print(f'Building index with {len(docs)} chunks...')

    for start in range(0, len(docs), batch_size):
        batch = docs[start : start + batch_size]
        vectorstore.add_documents(batch)
        print(f'Indexed {start + len(batch)}/{len(docs)} chunks')

    print('Index build complete.')
    print(f'Persist directory: {persist_directory}')
    print(f'Collection: {collection_name}')


def preferred_groups_for_query(query: str, config: dict[str, Any], top_files: int) -> tuple[str, list[str], dict[str, Any]]:
    summary = summarize_for_rag(query, config, top_n=top_files)
    route_name = summary['route']
    route_groups = config.get('query_routes', {}).get(route_name, {}).get('use', [])
    candidate_groups: list[str] = []
    for item in summary['candidate_documents']:
        if item['group'] not in candidate_groups:
            candidate_groups.append(item['group'])
    ordered_groups = [group for group in route_groups if group in candidate_groups]
    for group in candidate_groups:
        if group not in ordered_groups:
            ordered_groups.append(group)
    return route_name, ordered_groups, summary


def query_index(
    query: str,
    config: dict[str, Any],
    persist_directory: Path,
    collection_name: str,
    embedding_model: str,
    top_files: int,
    top_chunks: int,
) -> None:
    vectorstore = open_vectorstore(persist_directory, collection_name, embedding_model)
    route_name, preferred_groups, summary = preferred_groups_for_query(query, config, top_files=top_files)

    docs = []
    for group in preferred_groups:
        docs.extend(
            vectorstore.similarity_search(
                query,
                k=max(2, top_chunks),
                filter={'source_group': group},
            )
        )

    if not docs:
        docs = vectorstore.similarity_search(query, k=top_chunks)

    seen = set()
    results: list[dict[str, Any]] = []
    for doc in docs:
        key = (doc.metadata.get('source_path'), doc.metadata.get('chunk_id'))
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                'path': doc.metadata.get('source_path', ''),
                'group': doc.metadata.get('source_group', ''),
                'chunk_id': doc.metadata.get('chunk_id', -1),
                'text': doc.page_content,
            }
        )
        if len(results) >= top_chunks:
            break

    context = build_context_block(results)
    print('=' * 80)
    print('QUERY:', query)
    print('ROUTE:', route_name)
    print('PREFERRED_GROUPS:', preferred_groups)
    print('ANSWER_POLICY:', effective_answer_policy(query, summary, config))
    print('TOP_RESULTS:')
    for item in results:
        print(f"  - group={item['group']} chunk={item['chunk_id']} path={item['path']}")
    print('\n' + '=' * 80)
    print('CONTEXT_FOR_LLM:')
    print(context if context else '(no matching chunks)')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='LangChain + Chroma local RAG using kb-v1 config.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    build_parser = subparsers.add_parser('build', help='Build or rebuild the Chroma index')
    build_parser.add_argument('--persist-dir', default=str(DEFAULT_PERSIST_DIR))
    build_parser.add_argument('--collection', default=DEFAULT_COLLECTION)
    build_parser.add_argument('--embedding-model', default=DEFAULT_EMBEDDING_MODEL)
    build_parser.add_argument('--chunk-size', type=int, default=1200)
    build_parser.add_argument('--overlap', type=int, default=180)
    build_parser.add_argument('--batch-size', type=int, default=64)
    build_parser.add_argument('--reset', action='store_true')

    query_parser = subparsers.add_parser('query', help='Query the Chroma index')
    query_parser.add_argument('query')
    query_parser.add_argument('--persist-dir', default=str(DEFAULT_PERSIST_DIR))
    query_parser.add_argument('--collection', default=DEFAULT_COLLECTION)
    query_parser.add_argument('--embedding-model', default=DEFAULT_EMBEDDING_MODEL)
    query_parser.add_argument('--top-files', type=int, default=6)
    query_parser.add_argument('--top-chunks', type=int, default=5)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    if args.command == 'build':
        build_index(
            config=config,
            persist_directory=Path(args.persist_dir),
            collection_name=args.collection,
            embedding_model=args.embedding_model,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            batch_size=args.batch_size,
            reset=args.reset,
        )
        return

    if args.command == 'query':
        query_index(
            query=args.query,
            config=config,
            persist_directory=Path(args.persist_dir),
            collection_name=args.collection,
            embedding_model=args.embedding_model,
            top_files=args.top_files,
            top_chunks=args.top_chunks,
        )
        return

    raise ValueError(f'Unsupported command: {args.command}')


if __name__ == '__main__':
    main()



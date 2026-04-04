from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import pickle
import re
import sys
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from example_load_config import summarize_for_rag

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'retrieval-priority-v1.json'
CACHE_DIR = BASE_DIR / '.cache'
ASSIGNMENT_KEYWORDS = ('homework', 'assignment', '作业')



if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


def effective_answer_policy(query: str, summary: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    if summary.get('answer_policy'):
        return summary['answer_policy']
    lowered = query.lower()
    if any(keyword.lower() in lowered for keyword in ASSIGNMENT_KEYWORDS):
        return config.get('query_routes', {}).get('assignment_help', {}).get('answer_policy', {})
    return {}
def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def tokenize(text: str) -> list[str]:
    return re.findall(r'[\u4e00-\u9fff]+|[A-Za-z0-9_]+', text.lower())


class HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {'script', 'style', 'noscript'}:
            self._skip_depth += 1
        elif tag in {'p', 'div', 'section', 'article', 'br', 'li', 'h1', 'h2', 'h3', 'h4'}:
            self.parts.append('\n')

    def handle_endtag(self, tag: str) -> None:
        if tag in {'script', 'style', 'noscript'} and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in {'p', 'div', 'section', 'article', 'li', 'h1', 'h2', 'h3', 'h4'}:
            self.parts.append('\n')

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self.parts.append(data)

    def get_text(self) -> str:
        text = html.unescape(' '.join(self.parts))
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or '')
    return '\n\n'.join(parts)


def extract_html_text(path: Path) -> str:
    parser = HtmlTextExtractor()
    parser.feed(path.read_text(encoding='utf-8', errors='ignore'))
    return parser.get_text()


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        return extract_pdf_text(path)
    if suffix in {'.html', '.htm'}:
        return extract_html_text(path)
    return path.read_text(encoding='utf-8', errors='ignore')

def split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    return paragraphs or [text.strip()]


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    paragraphs = split_paragraphs(text)
    chunks: list[str] = []
    current = ''
    for paragraph in paragraphs:
        if len(paragraph) > chunk_size * 1.5:
            sentences = re.split(r'(?<=[.!?。！？])\s+', paragraph)
        else:
            sentences = [paragraph]
        for sentence in sentences:
            if not sentence:
                continue
            candidate = f'{current}\n\n{sentence}'.strip() if current else sentence
            if len(candidate) <= chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            if overlap and chunks:
                current = f"{chunks[-1][-overlap:]}\n{sentence}".strip()
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks


def cache_key(path: Path, chunk_size: int, overlap: int) -> str:
    signature = f'{path.resolve()}::{path.stat().st_mtime_ns}::{chunk_size}::{overlap}'
    return hashlib.sha256(signature.encode('utf-8')).hexdigest()


def load_or_build_chunks(path: Path, chunk_size: int, overlap: int) -> list[str]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{cache_key(path, chunk_size, overlap)}.pkl"
    if cache_path.exists():
        with cache_path.open('rb') as f:
            return pickle.load(f)
    chunks = chunk_text(extract_text(path), chunk_size=chunk_size, overlap=overlap)
    with cache_path.open('wb') as f:
        pickle.dump(chunks, f)
    return chunks


@dataclass
class ChunkRecord:
    path: str
    group: str
    route: str
    priority: int
    weight: float
    chunk_id: int
    text: str


def build_candidate_chunks(query: str, config: dict[str, Any], top_files: int = 6, chunk_size: int = 1200, overlap: int = 180) -> tuple[dict[str, Any], list[ChunkRecord]]:
    summary = summarize_for_rag(query, config, top_n=top_files)
    records: list[ChunkRecord] = []
    for item in summary['candidate_documents']:
        path = Path(item['path'])
        if not path.exists():
            continue
        for idx, chunk in enumerate(load_or_build_chunks(path, chunk_size=chunk_size, overlap=overlap)):
            records.append(ChunkRecord(path=str(path), group=item['group'], route=item['route'], priority=item['priority'], weight=item['weight'], chunk_id=idx, text=chunk))
    return summary, records


def score_chunks(query: str, chunks: list[ChunkRecord]) -> list[dict[str, Any]]:
    query_terms = tokenize(query)
    if not query_terms:
        return []
    doc_freq: Counter[str] = Counter()
    tokenized_chunks: list[list[str]] = []
    for chunk in chunks:
        tokens = tokenize(chunk.text)
        tokenized_chunks.append(tokens)
        for token in set(tokens):
            doc_freq[token] += 1
    total_docs = max(len(chunks), 1)
    scored: list[dict[str, Any]] = []
    for chunk, tokens in zip(chunks, tokenized_chunks):
        tf = Counter(tokens)
        score = 0.0
        for term in query_terms:
            if term in tf:
                score += tf[term] * (math.log((1 + total_docs) / (1 + doc_freq[term])) + 1.0)
        score = score * chunk.weight / max(chunk.priority, 1)
        if score > 0:
            scored.append({'score': score, 'path': chunk.path, 'group': chunk.group, 'route': chunk.route, 'chunk_id': chunk.chunk_id, 'text': chunk.text})
    scored.sort(key=lambda item: item['score'], reverse=True)
    return scored

def build_context_block(results: list[dict[str, Any]], max_chars: int = 5000) -> str:
    parts: list[str] = []
    total = 0
    for item in results:
        header = f"[SOURCE]\npath={item['path']}\ngroup={item['group']}\nchunk_id={item['chunk_id']}\n"
        block = f"{header}{item['text'].strip()}\n"
        if total + len(block) > max_chars and parts:
            break
        parts.append(block)
        total += len(block)
    return '\n'.join(parts)


def run_demo(query: str, config: dict[str, Any], top_files: int, top_chunks: int) -> None:
    summary, chunk_records = build_candidate_chunks(query, config, top_files=top_files)
    best = score_chunks(query, chunk_records)[:top_chunks]
    context = build_context_block(best)
    print('=' * 80)
    print('QUERY:', query)
    print('ROUTE:', summary['route'])
    policy = effective_answer_policy(query, summary, config)
    print('ANSWER_POLICY:', policy)
    print('CANDIDATE_FILES:', len(summary['candidate_documents']))
    print('INDEXED_CHUNKS:', len(chunk_records))
    print('TOP_CHUNKS:')
    for item in best:
        print(f"  - score={item['score']:.3f} group={item['group']} chunk={item['chunk_id']} path={item['path']}")
    print('\n' + '=' * 80)
    print('CONTEXT_FOR_LLM:')
    print(context[:8000] if context else '(no matching chunks)')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Minimal local RAG demo using the kb-v1 config.')
    parser.add_argument('query', nargs='?', default='How do I preprocess EEG data in Python?')
    parser.add_argument('--top-files', type=int, default=6)
    parser.add_argument('--top-chunks', type=int, default=5)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_demo(args.query, load_config(), top_files=args.top_files, top_chunks=args.top_chunks)


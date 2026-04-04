from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

from langchain_chroma_rag import (
    DEFAULT_COLLECTION,
    DEFAULT_EMBEDDING_MODEL,
    effective_answer_policy,
    load_config,
    open_vectorstore,
    preferred_groups_for_query,
)
from local_rag_demo import build_context_block

DEFAULT_ASCII_PERSIST_DIR = Path(r'C:\Users\Admin\bsp_kb_v1')
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / 'system-prompt.md'
DEFAULT_API_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
DEFAULT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
DEFAULT_API_KEY = os.getenv('OPENAI_API_KEY', '')
TEACHING_MODES = ('student', 'teacher')

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


@st.cache_resource(show_spinner=False)
def get_vectorstore(persist_dir: str, collection: str, embedding_model: str):
    return open_vectorstore(Path(persist_dir), collection, embedding_model)


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding='utf-8')


def apply_teaching_mode(base_policy: dict[str, Any], teaching_mode: str) -> dict[str, Any]:
    policy = dict(base_policy or {})
    if teaching_mode == 'teacher':
        return {
            'teaching_mode': 'teacher',
            'full_solution_allowed': True,
            'allow_complete_code': True,
            'allow_solution_key_style': True,
        }
    policy['teaching_mode'] = 'student'
    policy['strict_hint_only'] = True
    policy.setdefault('hints_only', True)
    policy.setdefault('no_final_submission', True)
    policy.setdefault('allow_partial_derivation', True)
    policy.setdefault('allow_debugging_guidance', True)
    return policy


def build_reference_list(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in results:
        path = item.get('path', '')
        if not path or path in seen:
            continue
        seen.add(path)
        refs.append(
            {
                'file_name': item.get('file_name') or Path(path).name,
                'group': item.get('group', ''),
                'path': path,
            }
        )
    return refs


def run_query(
    query: str,
    config: dict[str, Any],
    persist_dir: str,
    collection: str,
    embedding_model: str,
    top_files: int,
    top_chunks: int,
    teaching_mode: str,
) -> dict[str, Any]:
    vectorstore = get_vectorstore(persist_dir, collection, embedding_model)
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
                'file_name': doc.metadata.get('file_name', ''),
                'text': doc.page_content,
            }
        )
        if len(results) >= top_chunks:
            break

    base_policy = effective_answer_policy(query, summary, config)
    answer_policy = apply_teaching_mode(base_policy, teaching_mode)
    return {
        'query': query,
        'route': route_name,
        'preferred_groups': preferred_groups,
        'teaching_mode': teaching_mode,
        'answer_policy': answer_policy,
        'results': results,
        'references': build_reference_list(results),
        'context': build_context_block(results),
    }


def render_result_card(index: int, item: dict[str, Any]) -> None:
    label = f"{index}. {item['group']} | chunk {item['chunk_id']} | {item['file_name'] or Path(item['path']).name}"
    with st.expander(label, expanded=index == 1):
        st.caption(item['path'])
        st.text_area('Chunk Text', value=item['text'], height=220, key=f'chunk_text_{index}')


def render_reference_list(references: list[dict[str, str]]) -> None:
    if not references:
        st.write('(none)')
        return
    for ref in references:
        st.markdown(f"- `{ref['file_name']}`  ")
        st.caption(f"group={ref['group']} | {ref['path']}")


def build_user_prompt(query: str, retrieval_result: dict[str, Any]) -> str:
    policy = retrieval_result['answer_policy'] or {}
    policy_lines = [f"- Teaching mode: {retrieval_result['teaching_mode']}"]
    if retrieval_result['teaching_mode'] == 'student':
        policy_lines.append('- Student mode is strict. If the request could be coursework, provide hints, checkpoints, and method guidance only.')
        policy_lines.append('- Do not provide a final submission-ready answer or polished complete script.')
    else:
        policy_lines.append('- Teacher mode is enabled. Full solutions, complete code, and solution-key style explanations are allowed.')
    if policy.get('allow_partial_derivation'):
        policy_lines.append('- Partial derivations are allowed when useful for teaching.')
    if policy.get('allow_debugging_guidance'):
        policy_lines.append('- Debugging guidance is allowed.')

    context = retrieval_result['context'] or '(no retrieved context)'
    preferred_groups = ', '.join(retrieval_result['preferred_groups']) or '(none)'
    reference_names = ', '.join(ref['file_name'] for ref in retrieval_result.get('references', [])) or '(none)'

    return f"""
Question:
{query}

Route:
{retrieval_result['route']}

Teaching Mode:
{retrieval_result['teaching_mode']}

Preferred Source Groups:
{preferred_groups}

Reference Files:
{reference_names}

Answer Policy:
{chr(10).join(policy_lines)}

Retrieved Context:
{context}

Instruction:
Use the retrieved context first. If the context is incomplete, say what is missing. Cite source file names inline when helpful. Keep the answer concise and teaching-oriented.
""".strip()


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(item.get('text', ''))
            elif isinstance(item, str):
                parts.append(item)
        return '\n'.join(part for part in parts if part)
    return str(content)


def extract_delta_text(delta: Any) -> str:
    if isinstance(delta, dict):
        if 'content' in delta:
            return extract_text_content(delta.get('content', ''))
        return ''
    return extract_text_content(delta)


def build_request_payload(query: str, retrieval_result: dict[str, Any], system_prompt: str, model: str, temperature: float) -> dict[str, Any]:
    return {
        'model': model,
        'temperature': temperature,
        'stream': True,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': build_user_prompt(query, retrieval_result)},
        ],
    }


def stream_answer(
    query: str,
    retrieval_result: dict[str, Any],
    system_prompt: str,
    api_base: str,
    api_key: str,
    model: str,
    temperature: float,
    timeout_s: int,
):
    api_base = api_base.strip()
    api_key = api_key.strip()
    model = model.strip()

    if not api_key:
        raise RuntimeError('Missing API key. Fill in the API Key field or set OPENAI_API_KEY.')
    if not model:
        raise RuntimeError('Missing model name.')

    endpoint = api_base.rstrip('/') + '/chat/completions'
    payload = build_request_payload(query, retrieval_result, system_prompt, model, temperature)
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
    }

    timeout = httpx.Timeout(connect=20.0, read=float(timeout_s), write=30.0, pool=30.0)
    with httpx.Client(timeout=timeout) as client:
        with client.stream('POST', endpoint, headers=headers, json=payload) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:1200] if exc.response is not None else ''
                raise RuntimeError(f"HTTP {exc.response.status_code if exc.response is not None else ''}: {body}") from exc

            for line in response.iter_lines():
                if not line:
                    continue
                line = line.strip()
                if not line.startswith('data:'):
                    continue
                data_str = line[5:].strip()
                if data_str == '[DONE]':
                    break
                try:
                    payload = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = payload.get('choices', [])
                if not choices:
                    continue
                delta = choices[0].get('delta', {})
                text = extract_delta_text(delta)
                if text:
                    yield text


def main() -> None:
    st.set_page_config(page_title='Biomedical Signal Processing TA', page_icon='\U0001F9EA', layout='wide')

    config = load_config()
    system_prompt = load_system_prompt()
    default_persist = str(
        DEFAULT_ASCII_PERSIST_DIR if DEFAULT_ASCII_PERSIST_DIR.exists() else Path.cwd() / 'agent-template' / 'kb-v1' / 'chroma_db'
    )

    st.title('Biomedical Signal Processing TA')
    st.caption('LangChain + Chroma local retrieval plus answer generation for the undergraduate teaching agent.')

    with st.sidebar:
        st.subheader('Index Settings')
        persist_dir = st.text_input('Persist Directory', value=default_persist)
        collection = st.text_input('Collection', value=DEFAULT_COLLECTION)
        embedding_model = st.text_input('Embedding Model', value=DEFAULT_EMBEDDING_MODEL)
        top_files = st.slider('Preferred Files', min_value=2, max_value=12, value=6)
        top_chunks = st.slider('Returned Chunks', min_value=2, max_value=10, value=5)
        st.info('Use the ASCII-only persist directory if Chroma fails under the workspace path.')

        st.subheader('Teaching Mode')
        teaching_mode = st.selectbox('Audience Mode', options=TEACHING_MODES, format_func=lambda x: '学生模式' if x == 'student' else '教师模式')

        st.subheader('LLM Settings')
        enable_generation = st.toggle('Generate Answer', value=bool(DEFAULT_API_KEY))
        api_base = st.text_input('API Base', value=DEFAULT_API_BASE)
        model = st.text_input('Model', value=DEFAULT_MODEL)
        api_key = st.text_input('API Key', value=DEFAULT_API_KEY, type='password')
        temperature = st.slider('Temperature', min_value=0.0, max_value=1.0, value=0.2, step=0.05)
        timeout_s = st.slider('Timeout (s)', min_value=30, max_value=300, value=180, step=15)

    query = st.text_area(
        'Ask a question',
        value='ECG QRS detection MATLAB homework help',
        height=110,
        placeholder='Type an ECG, EMG, EEG, PPG, HDsEMG, or fNIRS teaching question...',
    )

    run = st.button('Run', type='primary', use_container_width=True)

    if not run:
        st.markdown('Try queries like `How do I preprocess EEG data in Python?` or `fNIRS baseline drift lab explanation`.')
        return

    if not query.strip():
        st.warning('Enter a question first.')
        return

    try:
        retrieval_result = run_query(
            query=query,
            config=config,
            persist_dir=persist_dir,
            collection=collection,
            embedding_model=embedding_model,
            top_files=top_files,
            top_chunks=top_chunks,
            teaching_mode=teaching_mode,
        )
    except Exception as exc:
        st.error(f'Retrieval failed: {exc}')
        st.stop()

    generated_answer = None
    generation_error = None

    info1, info2, info3, info4, info5 = st.columns(5)
    info1.metric('Route', retrieval_result['route'])
    info2.metric('Preferred Groups', len(retrieval_result['preferred_groups']))
    info3.metric('Returned Chunks', len(retrieval_result['results']))
    info4.metric('Generation', 'On' if enable_generation else 'Off')
    info5.metric('Mode', '学生' if teaching_mode == 'student' else '教师')

    if enable_generation:
        st.subheader('Generated Answer')
        answer_container = st.empty()
        try:
            generated_answer = answer_container.write_stream(
                stream_answer(
                    query=query,
                    retrieval_result=retrieval_result,
                    system_prompt=system_prompt,
                    api_base=api_base,
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    timeout_s=timeout_s,
                )
            )
        except httpx.ReadTimeout:
            generation_error = 'The API read timed out during streaming. Try raising Timeout to 240-300 seconds or lowering Returned Chunks to 2-3.'
        except Exception as exc:
            generation_error = str(exc)

        if generation_error:
            st.error(f'Answer generation failed: {generation_error}')
        elif not generated_answer:
            st.warning('The API stream completed but returned no text.')

    st.subheader('参考资料')
    render_reference_list(retrieval_result['references'])

    st.subheader('Policy')
    st.json(retrieval_result['answer_policy'] or {})

    st.subheader('Preferred Source Groups')
    st.write(retrieval_result['preferred_groups'])

    left, right = st.columns([1.1, 1])
    with left:
        st.subheader('Retrieved Chunks')
        if not retrieval_result['results']:
            st.warning('No chunks were returned.')
        for idx, item in enumerate(retrieval_result['results'], start=1):
            render_result_card(idx, item)

    with right:
        st.subheader('Context For LLM')
        st.text_area('Context', value=retrieval_result['context'], height=720)
        st.subheader('System Prompt')
        st.text_area('Prompt', value=system_prompt, height=260)


if __name__ == '__main__':
    main()
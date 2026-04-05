from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

from local_rag_demo import build_candidate_chunks, build_context_block, load_config, score_chunks

BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT_PATH = BASE_DIR.parent / 'system-prompt.md'
TEACHING_MODES = ('student', 'teacher')
DEFAULT_TOP_FILES = 6
DEFAULT_TOP_CHUNKS = 4

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    'App Default': {
        'api_base': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
        'key_secret': 'OPENAI_API_KEY',
        'base_secret': 'OPENAI_BASE_URL',
        'model_secret': 'OPENAI_MODEL',
        'description': 'Use the app-wide OpenAI-compatible configuration from Streamlit secrets.',
    },
    'Groq': {
        'api_base': 'https://api.groq.com/openai/v1',
        'model': 'llama-3.3-70b-versatile',
        'key_secret': 'GROQ_API_KEY',
        'base_secret': 'GROQ_API_BASE',
        'model_secret': 'GROQ_MODEL',
        'description': 'Groq OpenAI-compatible endpoint. Fast and convenient for demos.',
    },
    'Gemini': {
        'api_base': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'model': 'gemini-3-flash-preview',
        'key_secret': 'GEMINI_API_KEY',
        'base_secret': 'GEMINI_API_BASE',
        'model_secret': 'GEMINI_MODEL',
        'description': 'Google Gemini OpenAI compatibility endpoint.',
    },
    'OpenRouter': {
        'api_base': 'https://openrouter.ai/api/v1',
        'model': 'openrouter/free',
        'key_secret': 'OPENROUTER_API_KEY',
        'base_secret': 'OPENROUTER_API_BASE',
        'model_secret': 'OPENROUTER_MODEL',
        'description': 'OpenRouter unified endpoint. `openrouter/free` is useful for zero-cost trials.',
    },
    'Custom': {
        'api_base': 'https://api.openai.com/v1',
        'model': '',
        'key_secret': 'CUSTOM_API_KEY',
        'base_secret': 'CUSTOM_API_BASE',
        'model_secret': 'CUSTOM_MODEL',
        'description': 'Bring your own OpenAI-compatible API base, model, and key.',
    },
}

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


def get_secret(name: str, default: Any = '') -> Any:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


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


def build_reference_list(
    results: list[dict[str, Any]],
    candidate_documents: list[dict[str, Any]] | None = None,
    limit: int = 8,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_ref(item: dict[str, Any]) -> None:
        path = str(item.get('path', '')).strip()
        if not path or path in seen:
            return
        seen.add(path)
        refs.append(
            {
                'file_name': Path(path).name,
                'group': str(item.get('group', '')).strip(),
                'path': path,
            }
        )

    for item in results:
        add_ref(item)
        if len(refs) >= limit:
            return refs

    for item in candidate_documents or []:
        add_ref(item)
        if len(refs) >= limit:
            break

    return refs


def run_retrieval(query: str, config: dict[str, Any], top_files: int, top_chunks: int, teaching_mode: str) -> dict[str, Any]:
    summary, chunk_records = build_candidate_chunks(query, config, top_files=top_files)
    scored = score_chunks(query, chunk_records)
    best = scored[:top_chunks]
    references = build_reference_list(best, summary.get('candidate_documents', []), limit=max(top_files, top_chunks))
    answer_policy = apply_teaching_mode(summary.get('answer_policy', {}), teaching_mode)
    return {
        'query': query,
        'route': summary['route'],
        'preferred_groups': list(dict.fromkeys(item['group'] for item in summary['candidate_documents'])),
        'teaching_mode': teaching_mode,
        'answer_policy': answer_policy,
        'results': best,
        'references': references,
        'context': build_context_block(best),
    }


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

    reference_names = ', '.join(ref['file_name'] for ref in retrieval_result['references']) or '(none)'
    preferred_groups = ', '.join(retrieval_result['preferred_groups']) or '(none)'

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
{retrieval_result['context']}

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


def resolve_provider_settings(provider_name: str) -> dict[str, str]:
    preset = PROVIDER_PRESETS[provider_name]
    api_base = str(get_secret(preset.get('base_secret', ''), preset['api_base']))
    model = str(get_secret(preset.get('model_secret', ''), preset['model']))
    api_key = str(get_secret(preset.get('key_secret', ''), ''))

    if provider_name == 'App Default':
        api_base = str(get_secret('OPENAI_BASE_URL', api_base or preset['api_base']))
        model = str(get_secret('OPENAI_MODEL', model or preset['model']))
        api_key = str(get_secret('OPENAI_API_KEY', api_key))

    return {
        'provider_name': provider_name,
        'api_base': api_base,
        'model': model,
        'api_key': api_key,
        'description': preset['description'],
    }


def build_provider_headers(provider_name: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    if provider_name == 'OpenRouter':
        referer = str(get_secret('OPENROUTER_HTTP_REFERER', '')).strip()
        title = str(get_secret('OPENROUTER_APP_TITLE', 'Biomedical Signal Processing TA')).strip()
        if referer:
            headers['HTTP-Referer'] = referer
        if title:
            headers['X-OpenRouter-Title'] = title
    return headers


def stream_answer(
    query: str,
    retrieval_result: dict[str, Any],
    system_prompt: str,
    provider_name: str,
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
        raise RuntimeError('Missing API key. Configure the provider key in Streamlit secrets or enter it in the sidebar.')
    if not model:
        raise RuntimeError('Missing model name.')
    if not api_base:
        raise RuntimeError('Missing API base URL.')

    endpoint = api_base.rstrip('/') + '/chat/completions'
    payload = {
        'model': model,
        'temperature': temperature,
        'stream': True,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': build_user_prompt(query, retrieval_result)},
        ],
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
    }
    headers.update(build_provider_headers(provider_name))

    timeout = httpx.Timeout(connect=20.0, read=float(timeout_s), write=30.0, pool=30.0)
    with httpx.Client(timeout=timeout) as client:
        with client.stream('POST', endpoint, headers=headers, json=payload) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = exc.response.text[:1200] if exc.response is not None else ''
                code = exc.response.status_code if exc.response is not None else ''
                raise RuntimeError(f'HTTP {code}: {body}') from exc
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
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = data.get('choices', [])
                if not choices:
                    continue
                text = extract_delta_text(choices[0].get('delta', {}))
                if text:
                    yield text


def render_reference_list(references: list[dict[str, str]]) -> None:
    if not references:
        st.write('(none)')
        return
    for ref in references:
        st.markdown(f"- `{ref['file_name']}`")
        st.caption(f"group={ref['group']} | {ref['path']}")


def render_result_card(index: int, item: dict[str, Any]) -> None:
    label = f"{index}. {item['group']} | chunk {item['chunk_id']} | {Path(item['path']).name}"
    with st.expander(label, expanded=index == 1):
        st.caption(item['path'])
        st.text_area('Chunk Text', value=item['text'], height=220, key=f'cloud_chunk_{index}')


def main() -> None:
    st.set_page_config(page_title='Biomedical Signal Processing TA', page_icon='🧪', layout='wide')

    config = load_config(BASE_DIR / 'retrieval-priority-v1.json')
    system_prompt = load_system_prompt()

    timeout_default = int(get_secret('OPENAI_TIMEOUT_SECONDS', 180))
    enable_teacher_mode = str(get_secret('ENABLE_TEACHER_MODE', 'false')).lower() == 'true'

    st.title('Biomedical Signal Processing TA')
    st.caption('Community Cloud edition: lightweight retrieval plus answer generation for undergraduate teaching.')

    with st.sidebar:
        st.subheader('Retrieval Settings')
        top_files = st.slider('Preferred Files', min_value=2, max_value=12, value=DEFAULT_TOP_FILES)
        top_chunks = st.slider('Returned Chunks', min_value=2, max_value=10, value=DEFAULT_TOP_CHUNKS)

        st.subheader('Teaching Mode')
        if enable_teacher_mode:
            teaching_mode = st.selectbox(
                'Audience Mode',
                options=TEACHING_MODES,
                format_func=lambda x: '学生模式' if x == 'student' else '教师模式',
            )
        else:
            teaching_mode = 'student'
            st.caption('学生模式已固定。如需开启教师模式，请在 secrets 中设置 `ENABLE_TEACHER_MODE=true`。')

        st.subheader('LLM Provider')
        provider_name = st.selectbox('Provider Preset', options=list(PROVIDER_PRESETS.keys()), index=0)
        provider_defaults = resolve_provider_settings(provider_name)
        st.caption(provider_defaults['description'])

        api_base = st.text_input('API Base', value=provider_defaults['api_base'])
        model = st.text_input('Model', value=provider_defaults['model'])
        api_key = st.text_input('API Key', value=provider_defaults['api_key'], type='password')

        st.subheader('Generation Settings')
        temperature = st.slider('Temperature', min_value=0.0, max_value=1.0, value=0.2, step=0.05)
        timeout_s = st.slider('Timeout (s)', min_value=30, max_value=300, value=timeout_default, step=15)
        st.caption('You can use the built-in presets or override them with your own OpenAI-compatible API settings.')

    query = st.text_area(
        'Ask a question',
        value='ECG QRS 检测方法',
        height=110,
        placeholder='Type an ECG, EMG, EEG, PPG, HDsEMG, or fNIRS teaching question...',
    )

    run = st.button('Run', type='primary', use_container_width=True)

    if not run:
        st.markdown('Try queries like `EEG预处理的基本步骤` or `fNIRS baseline drift lab explanation`.')
        return

    if not query.strip():
        st.warning('Enter a question first.')
        return

    with st.spinner('Retrieving context...'):
        retrieval_result = run_retrieval(query, config, top_files=top_files, top_chunks=top_chunks, teaching_mode=teaching_mode)

    generated_answer = None
    generation_error = None

    info1, info2, info3, info4, info5, info6 = st.columns(6)
    info1.metric('Route', retrieval_result['route'])
    info2.metric('Preferred Groups', len(retrieval_result['preferred_groups']))
    info3.metric('Returned Chunks', len(retrieval_result['results']))
    info4.metric('Generation', 'On' if bool(api_key.strip()) else 'Off')
    info5.metric('Mode', '学生' if teaching_mode == 'student' else '教师')
    info6.metric('Provider', provider_name)

    st.subheader('Generated Answer')
    answer_container = st.empty()
    if api_key.strip():
        try:
            generated_answer = answer_container.write_stream(
                stream_answer(
                    query=query,
                    retrieval_result=retrieval_result,
                    system_prompt=system_prompt,
                    provider_name=provider_name,
                    api_base=api_base,
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    timeout_s=timeout_s,
                )
            )
        except httpx.ReadTimeout:
            generation_error = 'The API read timed out during streaming. Try raising Timeout or lowering Returned Chunks.'
        except Exception as exc:
            generation_error = str(exc)
    else:
        generation_error = 'No API key configured. Add a provider key in Streamlit secrets or enter one in the sidebar.'

    if generation_error:
        st.error(f'Answer generation failed: {generation_error}')
    elif not generated_answer:
        st.warning('The API stream completed but returned no text.')

    st.subheader('Reference Materials')
    render_reference_list(retrieval_result['references'])

    st.subheader('Policy')
    st.json(retrieval_result['answer_policy'] or {})

    with st.expander('Active API Configuration', expanded=False):
        st.code(
            f'Provider: {provider_name}\nAPI Base: {api_base.strip()}\nModel: {model.strip()}\nAPI Key: {'*' * min(len(api_key.strip()), 8) if api_key.strip() else '(empty)'}',
            language='text',
        )

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


if __name__ == '__main__':
    main()

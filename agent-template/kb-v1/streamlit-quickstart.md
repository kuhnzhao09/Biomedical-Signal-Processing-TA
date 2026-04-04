# Streamlit Quick Start

## 1. Install Streamlit

```bash
pip install -r agent-template/kb-v1/requirements-streamlit.txt
```

## 2. Make sure the Chroma index already exists

Recommended on this machine:

```bash
python agent-template/kb-v1/langchain_chroma_rag.py build --reset --persist-dir C:\Users\Admin\bsp_kb_v1
```

## 3. Launch the web app

```bash
streamlit run agent-template/kb-v1/streamlit_app.py
```

## 4. In the sidebar

Use this persist directory first:

```text
C:\Users\Admin\bsp_kb_v1
```

This avoids the Windows path issue we hit with Chroma under the Chinese workspace path.

## 5. Enable answer generation

Fill in these fields in the sidebar:

- `API Base`
- `API Key`
- `Model`

The app calls an OpenAI-compatible `chat/completions` endpoint with `stream=true` for token streaming. If these are left empty, the page still works in retrieval-only mode.

Environment variables also work:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
OPENAI_MODEL
```

## 6. What the page shows

- Routed query type
- Answer policy
- Preferred source groups
- Retrieved chunks
- A ready-to-send `Context For LLM` block
- A generated teaching answer when API settings are configured


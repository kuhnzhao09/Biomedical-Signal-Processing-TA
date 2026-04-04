# LangChain + Chroma Quick Start

## 1. Install dependencies

```bash
pip install -r agent-template/kb-v1/requirements-langchain-chroma.txt
```

## 2. Build the local vector index

```bash
python agent-template/kb-v1/langchain_chroma_rag.py build --reset
```

Default settings:

- Persist directory: `agent-template/kb-v1/chroma_db`
- Collection: `biomedical_signal_processing_v1`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`

## 3. Query the index

```bash
python agent-template/kb-v1/langchain_chroma_rag.py query "ECG QRS detection MATLAB homework help" --top-files 5 --top-chunks 4
```

## 4. What the script does

- Reads `retrieval-priority-v1.json`
- Builds chunks from the configured default source groups
- Stores vectors in Chroma
- Routes each query using the same kb-v1 rules
- Searches preferred source groups first
- Prints a `CONTEXT_FOR_LLM` block for your model layer

## 5. Typical integration flow

1. Run `build` when materials change.
2. Run `query` or call `query_index(...)` from your application.
3. Pass the returned context into your chat model.
4. Enforce the assignment hint policy at the answer layer.

## 6. Notes

- The first build may take time because embeddings are computed for all chunks.
- If you change chunk size or overlap, rebuild with `--reset`.
- If `langchain_huggingface` is unavailable, the script can also work with the community HuggingFace embeddings backend if installed.

# Streamlit Community Cloud Deployment

## Recommended app entry

Use this file as the app entrypoint on Streamlit Community Cloud:

`agent-template/kb-v1/streamlit_cloud_app.py`

This cloud edition avoids local Chroma persistence and instead uses lightweight retrieval from the project files, which is more suitable for Community Cloud.

## Repository requirements

The repository root should contain:

- `requirements.txt`
- `.streamlit/secrets.toml.example`
- `agent-template/kb-v1/streamlit_cloud_app.py`

## Secrets to configure in Streamlit Cloud

Create app secrets with values like:

```toml
OPENAI_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
OPENAI_API_KEY = "your_real_key"
OPENAI_MODEL = "kimi-k2.5"
OPENAI_TIMEOUT_SECONDS = 180
ENABLE_TEACHER_MODE = false
```

## Deploy steps

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Click `Create app`.
4. Select your repository and branch.
5. Set the main file to `agent-template/kb-v1/streamlit_cloud_app.py`.
6. Add the secrets above in the app settings.
7. Deploy.

## Student-facing recommendation

- Keep `ENABLE_TEACHER_MODE = false`.
- Do not expose API Base, API Key, or model controls to students.
- Use student mode as the default public mode.

## Notes

- Community Cloud is suitable for lightweight course usage, demos, and pilot deployment.
- The local Chroma engineering build is still useful for your own offline development, but not ideal as the primary Cloud entrypoint.

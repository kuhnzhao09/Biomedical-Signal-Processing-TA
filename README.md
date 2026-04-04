# Biomedical Signal Processing TA

一个面向本科教学场景的生物医学信号处理智能助教项目，支持本地检索增强问答、`Streamlit` 网页交互，以及 `Streamlit Community Cloud` 部署。

## 项目目标

这个项目用于快速搭建一个“生物医学信号处理教学助教”原型，适合课程答疑、概念讲解、实验指导和提示式作业辅导。

当前默认定位：
- 课程对象：本科生
- 软件环境：`MATLAB` + `Python`
- 优先信号类型：`ECG`、`EMG`、`HDsEMG`、`EEG`、`PPG`、`fNIRS`
- 作业策略：学生模式下只给提示，不直接给提交级答案

## 当前能力

- 教学助教技能模板
- 通用版系统提示词
- 知识库清单与检索优先级配置
- 本地最小 RAG 示例
- `LangChain + Chroma` 工程版检索
- `Streamlit` 本地网页应用
- `Streamlit Community Cloud` 轻量部署版
- 学生模式 / 教师模式切换
- 参考资料列表展示
- OpenAI-compatible 接口流式回答生成

## 仓库结构

```text
.
├─ .streamlit/
│  └─ secrets.toml.example
├─ agent-template/
│  ├─ system-prompt.md
│  ├─ knowledge-base-template.md
│  ├─ quick-start.md
│  └─ kb-v1/
│     ├─ streamlit_cloud_app.py
│     ├─ streamlit_app.py
│     ├─ langchain_chroma_rag.py
│     ├─ local_rag_demo.py
│     ├─ retrieval-priority-v1.json
│     └─ ...
├─ skills/
│  └─ biomedical-signal-processing-teaching-assistant/
├─ requirements.txt
└─ STREAMLIT_COMMUNITY_CLOUD.md
```

## 推荐使用方式

### 1. 直接部署到 Streamlit Community Cloud

这是最适合给学生试用的方式。

入口文件：

```text
agent-template/kb-v1/streamlit_cloud_app.py
```

依赖文件：

```text
requirements.txt
```

Secrets 示例见：

```text
.streamlit/secrets.toml.example
```

详细说明见：

```text
STREAMLIT_COMMUNITY_CLOUD.md
```

### 2. 本地运行完整版

如果你希望使用本地 `Chroma` 向量库和更完整的检索流程，可以使用本地版应用。

安装依赖：

```bash
pip install -r requirements.txt
pip install -r agent-template/kb-v1/requirements-langchain-chroma.txt
pip install -r agent-template/kb-v1/requirements-streamlit.txt
```

启动本地网页：

```bash
streamlit run agent-template/kb-v1/streamlit_app.py
```

## Streamlit Community Cloud 部署最短步骤

1. 将本仓库推送到 GitHub。
2. 登录 `Streamlit Community Cloud`。
3. 新建应用并选择本仓库。
4. Main file path 填写：

```text
agent-template/kb-v1/streamlit_cloud_app.py
```

5. 在 Cloud Secrets 中填写：

```toml
OPENAI_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"
OPENAI_API_KEY = "your_api_key_here"
OPENAI_MODEL = "kimi-k2.5"
OPENAI_TIMEOUT_SECONDS = 180
ENABLE_TEACHER_MODE = false
```

6. 部署完成后，将链接发给学生使用。

## 学生模式与教师模式

- 学生模式：默认推荐，强调概念讲解、实验步骤、解题提示，不提供提交级答案。
- 教师模式：可用于备课、生成完整示例、出题和参考答案草稿。

如果面向学生公开部署，建议固定为学生模式，并关闭教师模式入口。

## 资料与版权说明

当前仓库默认不包含 `materials/` 下的大多数资料文件。

原因：
- 部分文件体积较大，不适合直接进入仓库。
- 部分文件可能存在版权或再分发限制。
- 公开部署版优先保留代码、配置、提示词和知识库结构，而不是直接分发全文资料。

## 关键文件

- `Streamlit Cloud` 入口：`agent-template/kb-v1/streamlit_cloud_app.py`
- 本地版入口：`agent-template/kb-v1/streamlit_app.py`
- 工程版检索：`agent-template/kb-v1/langchain_chroma_rag.py`
- 最小本地检索：`agent-template/kb-v1/local_rag_demo.py`
- 检索配置：`agent-template/kb-v1/retrieval-priority-v1.json`
- 技能模板：`skills/biomedical-signal-processing-teaching-assistant/SKILL.md`

## 后续建议

- 用你自己的课件、实验指导书和习题逐步替换通用资料
- 为不同章节补充 FAQ 和示例代码
- 在公开部署版中隐藏模型配置，只保留学生输入区
- 后续可加入登录、教师入口保护、作业场景更严格的拦截规则

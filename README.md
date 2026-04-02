# Alibaba CN Knowledge Base Query (RAG)

An [OpenClaw](https://github.com/openclaw/openclaw) skill for querying [Alibaba Cloud Bailian (百炼)](https://bailian.console.aliyun.com) Knowledge Base via RAG.

Upload your documents to Bailian → this skill lets your AI agent answer questions using your internal knowledge base with citations.

## Features

- 🔍 RAG-powered Q&A from your Bailian knowledge base
- 📑 Returns answers with document citations
- 🔒 Credentials stored separately in `CONFIG.md` (gitignored)
- 🚀 First-time setup wizard guides users through configuration
- 🤖 MCP tool support — registers as `bailian-kb` in mcporter for full OpenClaw integration
- 🛠️ One-command install script (`install.sh`) handles everything

## Prerequisites

- Python 3.8+
- `requests` package (`pip install requests`)
- (Optional but recommended) `mcporter` for MCP tool mode: `npm i -g mcporter`
- An Alibaba Cloud account with [Bailian (百炼)](https://bailian.console.aliyun.com) access
- A Bailian Knowledge Base with documents uploaded
- A Bailian Application with the Knowledge Base attached

## Quick Install

```bash
git clone https://github.com/mismcinffh-svg/bailian-kb-query.git
cd bailian-kb-query
bash scripts/install.sh
```

The install script will:
1. Check Python 3 and mcporter are available
2. Register `bailian-kb` as an MCP tool via mcporter
3. Create `CONFIG.md` from the template
4. Tell you next steps

Then edit `CONFIG.md` and add your 4 credentials (see below).

## Setup Credentials

Edit `CONFIG.md` and fill in these 4 values:

| Field | Where to find |
|---|---|
| `DASHSCOPE_API_KEY` | [bailian.console.aliyun.com](https://bailian.console.aliyun.com) → Avatar → API Key Management |
| `BAILIAN_WORKSPACE_ID` | Bailian Console → Top-left workspace dropdown |
| `BAILIAN_KB_ID` | Bailian Console → Knowledge Base → Your KB → ID |
| `BAILIAN_APP_ID` | Bailian Console → App Management → Your App → ID |

## Usage

### MCP Tool Mode (Recommended)

After running `install.sh`, the tool is registered and can be called directly:

```bash
mcporter call bailian-kb.bailian-kb question="公司有幾天年假？"
```

### CLI Mode

```bash
python3 scripts/bailian-query.py "你的问题"
```

### In OpenClaw Agents

When an agent receives a question matching these trigger words, it will automatically use this skill:
> knowledge base, internal docs, company policy, employee handbook, search docs, find info, 知識庫, 內部文檔, 公司政策, 差旅, 報銷, 出差, claim

## Architecture

```
User question → bailian-query.py → Bailian Application API → RAG retrieval → Answer with citations
```

Two execution modes:
- **CLI mode**: Direct script execution with question as argument
- **MCP mode**: Script acts as MCP stdio server, mcporter registers it as `bailian-kb` tool

## Key Technical Decisions

### 1. API Approach (Tested 3 methods)
| Method | Result |
|---|---|
| OpenAI compat + `knowledge_base` extra_body | ❌ Model hallucinated, didn't actually search KB |
| DashScope Retrieve API (`/indices/{id}/retrieve`) | ❌ Returns HTML, endpoint incorrect for API Key auth |
| **Bailian Application API** (`/apps/{APP_ID}/completion`) | ✅ Works perfectly with `has_thoughts: true` |

### 2. Credential Management
- Credentials stored in `CONFIG.md` (gitignored)
- `CONFIG.example.md` as template for sharing
- Script reads CONFIG.md at runtime via regex parser
- First-time use: script returns `SETUP_REQUIRED` JSON → agent guides user through 4-step setup

### 3. Required IDs
| ID | Format | Source |
|---|---|---|
| `DASHSCOPE_API_KEY` | `sk-xxx` | Bailian Console → API Key Management |
| `BAILIAN_WORKSPACE_ID` | `llm-xxx` | Console → Workspace dropdown |
| `BAILIAN_KB_ID` | ~10 char alphanumeric | Console → Knowledge Base → KB card |
| `BAILIAN_APP_ID` | 32-char hex | Console → App Management → App card |

## Lessons Learned
1. Bailian KB **must** be accessed through Application API — no shortcut via OpenAI compat mode
2. Application needs to be created manually in console and linked to KB
3. Vague queries ("list all files") trigger fallback; specific queries work perfectly
4. Account must have positive balance even for free tier usage (Arrearage error)
5. `has_thoughts: true` + `doc_reference_type: "simple"` returns retrieval process and citations

## Cost
- ~4,000-6,000 tokens per query
- Model: qwen-plus (configurable in Bailian console)
- Alibaba Cloud Bailian has free tier credits

## Files in Repo
```
bailian-kb-query/
├── README.md
├── SKILL.md
├── CONFIG.example.md
├── .gitignore
├── scripts/
│   ├── bailian-query.py      # CLI + MCP dual mode
│   ├── bailian-query.sh
│   └── install.sh            # One-command setup + MCP registration
```

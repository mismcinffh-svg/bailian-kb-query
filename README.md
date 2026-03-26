# bailian-kb-query

An [OpenClaw](https://github.com/openclaw/openclaw) skill for querying [Alibaba Cloud Bailian (百炼)](https://bailian.console.aliyun.com) Knowledge Base via RAG.

Upload your documents to Bailian → this skill lets your AI agent answer questions using your internal knowledge base with citations.

## Features

- 🔍 RAG-powered Q&A from your Bailian knowledge base
- 📑 Returns answers with document citations
- 🔒 Credentials stored separately in `CONFIG.md` (gitignored)
- 🚀 First-time setup wizard guides users through configuration
- 🤖 Designed for OpenClaw multi-agent systems

## Prerequisites

- Python 3.8+
- `requests` package (`pip install requests`)
- An Alibaba Cloud account with [Bailian (百炼)](https://bailian.console.aliyun.com) access
- A Bailian Knowledge Base with documents uploaded
- A Bailian Application with the Knowledge Base attached

## Setup

### 1. Install the skill

Copy this directory to your OpenClaw workspace:

```bash
cp -r bailian-kb-query ~/.openclaw/workspace/skills/bailian-kb
```

### 2. Configure credentials

Copy the example config and fill in your values:

```bash
cd ~/.openclaw/workspace/skills/bailian-kb
cp CONFIG.example.md CONFIG.md
# Edit CONFIG.md with your actual credentials
```

You'll need 4 values from your Bailian console:

| Field | Where to find it |
|---|---|
| `DASHSCOPE_API_KEY` | Avatar → API Key Management |
| `BAILIAN_WORKSPACE_ID` | Top-left workspace dropdown |
| `BAILIAN_KB_ID` | Knowledge Base → Your KB → ID |
| `BAILIAN_APP_ID` | App Management → Your App → App ID |

### 3. Test

```bash
python3 scripts/bailian-query.py "What documents are in the knowledge base?"
```

## Usage

### Direct CLI

```bash
python3 scripts/bailian-query.py "What is the company travel policy?"
```

### As OpenClaw Skill

Once installed, OpenClaw agents will automatically trigger this skill when users ask questions about internal documents, company policies, or knowledge base content.

## File Structure

```
bailian-kb-query/
├── README.md            # This file
├── SKILL.md             # OpenClaw skill definition & agent instructions
├── CONFIG.example.md    # Config template (safe to share)
├── CONFIG.md            # Your credentials (gitignored)
├── .gitignore           # Excludes CONFIG.md
└── scripts/
    └── bailian-query.py # Main query script
```

## How It Works

1. Script reads credentials from `CONFIG.md`
2. Sends query to Bailian Application API (`/api/v1/apps/{APP_ID}/completion`)
3. Bailian automatically retrieves relevant document chunks from the knowledge base
4. Returns AI-generated answer with document citations

## Cost

- Bailian offers free tier credits for new accounts
- Typical query: ~4,000-6,000 tokens (input + output)
- Model: `qwen-plus` (configurable in Bailian console)

## License

MIT

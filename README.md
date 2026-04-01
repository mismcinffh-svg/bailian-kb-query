# Bailian KB Query — Development Notes

## Project Overview
- **Repo**: https://github.com/mismcinffh-svg/bailian-kb-query
- **Skill location**: `~/.openclaw/workspace/skills/bailian-kb/`
- **Status**: ✅ v1.0 Complete & Published
- **Date**: 2026-03-26

## What It Does
OpenClaw skill that queries Alibaba Cloud Bailian (百炼) Knowledge Base via RAG.
Users upload documents to Bailian → agent answers questions from the KB with citations.

## Architecture
```
User question → bailian-query.py → Bailian Application API → RAG retrieval → Answer with citations
```

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
└── scripts/
    ├── bailian-query.py
    └── bailian-query.sh
```

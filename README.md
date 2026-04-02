# Bailian KB Query

An [OpenClaw](https://github.com/openclaw/openclaw) skill for querying
[Alibaba Cloud Bailian (百炼)](https://bailian.console.aliyun.com) Knowledge Base via RAG.

Upload documents to Bailian → the agent answers questions from your internal
knowledge base with citations.

## Features

- 🔍 RAG-powered Q&A from your Bailian knowledge base
- 📑 Returns answers with document citations
- 🤖 MCP tool — registers as `bailian-kb` in mcporter, discoverable by all agents
- 🛠️ One-command install (`install.sh`) handles MCP registration + CONFIG setup
- 🔒 Credentials stored in `CONFIG.md` (gitignored)

---

## 🤖 For AI Agents — Complete Setup in 5 Steps

Any OpenClaw agent can install and use this skill by following these steps:

### Step 1 — Clone the repo

```bash
git clone https://github.com/mismcinffh-svg/bailian-kb-query.git \
  ~/.openclaw/workspace/skills/bailian-kb

cd ~/.openclaw/workspace/skills/bailian-kb
```

### Step 2 — Run the install script

```bash
bash scripts/install.sh
```

This script:
1. Checks Python 3 is available
2. Registers `bailian-kb` as an MCP tool via mcporter
3. Creates `CONFIG.md` from the template (if not already present)

### Step 3 — Add your credentials

Edit `CONFIG.md` and fill in all 4 values from
https://bailian.console.aliyun.com:

| Field | Where to find it |
|---|---|
| `DASHSCOPE_API_KEY` | Avatar → API Key Management |
| `BAILIAN_WORKSPACE_ID` | Top-left workspace dropdown |
| `BAILIAN_KB_ID` | Knowledge Base → your KB → ID |
| `BAILIAN_APP_ID` | App Management → your app → ID |

### Step 4 — Verify the setup

```bash
mcporter call bailian-kb.bailian-kb question="hello"
# Expected: JSON response with an answer
```

If you see `SETUP_REQUIRED`, the credentials are missing — double-check CONFIG.md.

### Step 5 — You're done

The tool is now registered. When a user asks about internal documents,
company policies, HR, travel, reimbursement, etc., the agent will use it.

---

## Prerequisites

- Python 3.8+
- `requests` package: `pip install requests`
- (Optional but recommended) `mcporter`: `npm i -g mcporter`
- An Alibaba Cloud Bailian account with uploaded documents and a linked Application

---

## Usage Modes

### MCP Tool (Recommended)

After `install.sh`, the tool is registered and callable via mcporter:

```bash
mcporter call bailian-kb.bailian-kb question="公司有幾天年假？"
```

List all registered tools:
```bash
mcporter list
```

### CLI Direct

```bash
python3 scripts/bailian-query.py "你的问题"
```

---

## Trigger Words

This skill activates when users ask about:
> knowledge base, internal docs, company policy, employee handbook,
> search docs, find info, 知識庫, 內部文檔, 公司政策, 差旅, 報銷, 出差, claim

---

## Key Technical Decisions

### API Approach (3 methods tested)

| Method | Result |
|---|---|
| OpenAI compat + `knowledge_base` extra_body | ❌ Model hallucinated |
| DashScope Retrieve API | ❌ HTML returned, auth failed |
| **Bailian Application API** (`/apps/{APP_ID}/completion`) | ✅ Perfect with `has_thoughts: true` |

### Required Credentials

| ID | Format | Source |
|---|---|---|
| `DASHSCOPE_API_KEY` | `sk-xxx` | Bailian Console → API Key |
| `BAILIAN_WORKSPACE_ID` | `llm-xxx` | Console → Workspace dropdown |
| `BAILIAN_KB_ID` | ~10 chars | Console → Knowledge Base → KB card |
| `BAILIAN_APP_ID` | 32-char hex | Console → App Management → App card |

### Bailian App Setup Checklist

1. Create a Knowledge Base → Upload your documents
2. Create an Application → Select model (recommend `qwen-plus`)
3. In the app's "Documents" section → Link your Knowledge Base → Save
4. Copy the Application ID → Paste into CONFIG.md

---

## Lessons Learned

1. Bailian KB **must** be accessed through Application API — no shortcut via OpenAI compat mode
2. Application must be manually linked to the KB in console
3. Specific questions work; vague queries ("list all files") trigger fallback
4. Account must have positive balance even for free tier (Arrearage error if not)
5. `has_thoughts: true` + `doc_reference_type: "simple"` returns retrieval process + citations

---

## Cost

- ~4,000–6,000 tokens per query
- Model: qwen-plus (configurable in Bailian console)
- Alibaba Cloud Bailian free tier credits available

---

## Repo Files

```
bailian-kb-query/
├── SKILL.md              ← Agent + human setup instructions
├── README.md             ← This file
├── CONFIG.example.md     ← Credential template (safe to share)
├── .gitignore            ← Ignores CONFIG.md
└── scripts/
    ├── bailian-query.py  ← Dual-mode: CLI + MCP stdio
    ├── bailian-query.sh  ← Bash wrapper
    └── install.sh        ← One-command setup (MCP registration)
```

---

## Troubleshooting

### `SETUP_REQUIRED` / `CONFIG_INCOMPLETE`

Credentials are missing in `CONFIG.md`. Fill in all 4 fields.

### `Arrearage error` / HTTP 400

Alibaba Cloud account has zero balance. Top up the account.

### HTTP 401 / 403

Wrong or expired `DASHSCOPE_API_KEY`. Regenerate at bailian.console.aliyun.com.

### mcporter not found

Install mcporter first: `npm i -g mcporter`

### MCP tool not showing in `mcporter list`

Re-run the registration:
```bash
mcporter config add bailian-kb \
  --stdio "python3 ~/.openclaw/workspace/skills/bailian-kb/scripts/bailian-query.py --mcp"
```

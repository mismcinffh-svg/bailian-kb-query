---
name: bailian-kb
description: >-
  Query Alibaba Cloud Bailian (百炼) Knowledge Base for RAG retrieval.
  Use when users ask about internal documents, company policies, procedures,
  product manuals, employee handbooks, project docs, technical docs, travel
  policies, reimbursement rules, HR regulations, or any internal knowledge.
  Also triggers when users explicitly ask to search the knowledge base or
  look up internal materials. Trigger words: knowledge base, internal docs,
  company policy, employee handbook, search docs, find info, 知識庫, 內部文檔,
  公司政策, 差旅, 報銷, 出差, claim.
---

# Bailian Knowledge Base RAG Query

Queries Alibaba Cloud Bailian (百炼) Application API for RAG-powered Q&A against
an attached knowledge base. Returns answers with document citations.

---

## 🤖 AGENT QUICK-START (Read This First)

If you are an AI agent installing this skill, follow these steps in order:

### Step 1 — Install the skill files

If the files are not yet on this machine:

```bash
git clone https://github.com/mismcinffh-svg/bailian-kb-query.git \
  ~/.openclaw/workspace/skills/bailian-kb

cd ~/.openclaw/workspace/skills/bailian-kb
```

### Step 2 — Run the setup script (registers MCP tool automatically)

```bash
bash scripts/install.sh
```

The install script will:
- Check Python 3 is available
- Register `bailian-kb` as an MCP tool via `mcporter`
- Create `CONFIG.md` from the template

### Step 3 — Configure credentials

Edit `CONFIG.md` and fill in the 4 required values. Get them from
https://bailian.console.aliyun.com:

| Config key | Where to find |
|---|---|
| `DASHSCOPE_API_KEY` | Avatar → API Key Management |
| `BAILIAN_WORKSPACE_ID` | Top-left workspace dropdown |
| `BAILIAN_KB_ID` | Knowledge Base → your KB → ID |
| `BAILIAN_APP_ID` | App Management → your app → ID |

### Step 4 — Verify it works

```bash
mcporter call bailian-kb.bailian-kb question="test query"
# Expected: JSON response with an answer (or SETUP_REQUIRED if not configured)
```

### Step 5 — Use it when triggered

When a user asks about internal knowledge, policies, procedures, travel,
reimbursement, HR, etc., call the tool:

```bash
mcporter call bailian-kb.bailian-kb question="<user's question>"
```

Or use the CLI directly:

```bash
python3 scripts/bailian-query.py "user's question here"
```

---

## First-Time Setup (Human Operator)

This skill requires 4 credentials stored in `CONFIG.md`.

### Check if configured

```bash
python3 scripts/bailian-query.py "test"
```

If the script returns `SETUP_REQUIRED`, follow the setup flow.

### Obtain credentials

1. **API Key** (`DASHSCOPE_API_KEY`)
   - Log in to https://bailian.console.aliyun.com
   - Click avatar (top-right) → API Key Management → Copy API Key

2. **Workspace ID** (`BAILIAN_WORKSPACE_ID`)
   - Bailian Console → Top-left workspace dropdown → Copy Workspace ID

3. **Knowledge Base ID** (`BAILIAN_KB_ID`)
   - Bailian Console → Knowledge Base → Click your KB → Copy ID

4. **Application ID** (`BAILIAN_APP_ID`)
   - Bailian Console → App Management → Create Agent App → Select model
   - In "Documents" section, link your knowledge base → Save
   - Copy Application ID

### Write configuration

Write to `CONFIG.md`:

```markdown
# Bailian KB Configuration

## API Key
DASHSCOPE_API_KEY=<your-api-key>

## Workspace ID
BAILIAN_WORKSPACE_ID=<your-workspace-id>

## Knowledge Base ID
BAILIAN_KB_ID=<your-kb-id>

## Application ID
BAILIAN_APP_ID=<your-app-id>
```

---

## Architecture

```
User question
    │
    ├─ CLI mode ──────────────→ python3 bailian-query.py "Q"
    │                                        │
    │                                        ▼
    │                              Bailian Application API
    │                                        │
    │                                        ▼
    └─ MCP mode ──────────────→ mcporter call bailian-kb.bailian-kb question="Q"
                                 (bailian-query.py --mcp in stdio mode)
                                              │
                                              ▼
                                    Bailian Application API
```

## Workflow

1. Receive a question matching trigger words (知識庫, internal docs, company policy, etc.)
2. Call via CLI or MCP tool
3. Return the answer with document citations — **never fabricate**

## Notes

- Specific questions work best; vague queries ("list all docs") may trigger fallback
- Never return answers not from the knowledge base
- Always preserve doc_references so users know the source
- If errors occur: check API Key validity and account balance
- `CONFIG.md` contains credentials — **never commit to Git**
- Timeout is 120s (KB retrieval can be slow)
- After `install.sh` runs once, `mcporter list` will show `bailian-kb` automatically

## Files in This Repo

```
bailian-kb-query/
├── SKILL.md              ← This file (agent + human instructions)
├── README.md             ← Full documentation
├── CONFIG.example.md     ← Credential template
├── .gitignore            ← Ignores CONFIG.md
└── scripts/
    ├── bailian-query.py  ← Dual-mode: CLI + MCP stdio
    ├── bailian-query.sh  ← Bash wrapper
    └── install.sh        ← One-command setup (MCP registration + CONFIG)
```

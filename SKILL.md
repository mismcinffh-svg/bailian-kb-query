---
name: bailian-kb
description: >-
  Query Alibaba Cloud Bailian (百炼) Knowledge Base for RAG retrieval with image support.
  Use when users ask about internal documents, company policies, procedures,
  product manuals, employee handbooks, project docs, technical docs, travel
  policies, reimbursement rules, HR regulations, or any internal knowledge.
  Also triggers when users explicitly ask to search the knowledge base or
  look up internal materials. **Supports 圖文並茂回覆 (rich text with images)**.
  Trigger words: knowledge base, internal docs, company policy, employee handbook,
  search docs, find info, 知識庫, 內部文檔, 公司政策, 差旅, 報銷, 出差, claim.
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
2. Call via CLI: `python3 scripts/bailian-query.py "question"`
3. **Parse the JSON response** (see Output Format below)
4. **Send in step-by-step format** (see Telegram Response Format below)
5. Return the answer with document citations and any images — **never fabricate**

## Output Format (JSON)

The script returns structured JSON:

```json
{
  "steps": [
    {
      "number": 1,
      "title": "Step title",
      "text": "Additional step details (if any)",
      "image": "/tmp/.../0.png"  // null if no image
    },
    ...
  ],
  "images": [
    {"path": "/tmp/.../0.png", "alt": "description"},
    ...
  ],
  "model": "qwen-max-2025-01-25",
  "temp_dir": "/tmp/bailian_images_xxx",
  "doc_references": [...]
}
```

## Telegram Response Format

**IMPORTANT**: Always send in step-by-step format:

1. For each step in `steps` array:
   - Send text message: "**Step N：標題**\n內容"
   - If step has image, send image immediately after

2. If no steps (pure text), send as single message

3. Clean up `temp_dir` after all messages sent

**Example flow**:
```
Message 1: "**Step 1：登錄**\n登錄網址：http://..."
Message 2: [image /tmp/bailian_images_xxx/0.png]
Message 3: "**Step 2：選擇平台**\n選擇「行政營運...」"
Message 4: [image /tmp/bailian_images_xxx/1.png]
...
```

**Rules**:
- Each step = 1 text message + 1 image (if available)
- Use "**Step N：標題**" format for step headers
- Send images immediately after their corresponding step
- Do NOT batch all text then all images
- Clean up temporary directory after sending

## Image Support (圖文並茂回覆)

This skill supports **圖文並茂回覆** when:
1. Knowledge base is configured with **使用場景: 圖文並茂回覆**
2. Application uses **千問-Plus** or **千問-Plus-Latest** model
3. Documents contain embedded images

When images are available:
- Script downloads images to temporary directory
- Returns JSON with `text` and `images` fields
- **IMPORTANT**: Send images in step-by-step format (see Telegram Response Format above)
- Never batch all text then all images — maintain step-to-image correspondence
- Temporary files are cleaned up after all messages are sent

## Notes

- Specific questions work best; vague queries ("list all docs") may trigger fallback
- Never return answers not from the knowledge base
- Always preserve doc_references so users know the source
- **Image support**: When KB is configured for 圖文並茂回覆, images are automatically downloaded and attached
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

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

This skill queries Alibaba Cloud Bailian (百炼) Application API for RAG-powered Q&A.
The Application has a knowledge base attached and automatically retrieves relevant
document chunks to generate answers with citations.

## First-Time Setup

This skill requires 4 credentials stored in `CONFIG.md`. On first use, guide the
user through the setup process.

### Check if configured

```bash
python3 <SKILL_DIR>/scripts/bailian-query.py "test"
```

If the script returns `SETUP_REQUIRED`, follow the setup flow below.

### Guide user to obtain IDs

Walk the user through each step:

1. **API Key** (`DASHSCOPE_API_KEY`)
   - Log in to https://bailian.console.aliyun.com
   - Click avatar (top-right) → API Key Management → Copy API Key
   - Format: `sk-xxxxxxx`

2. **Workspace ID** (`BAILIAN_WORKSPACE_ID`)
   - Bailian Console → Top-left workspace dropdown → Copy Workspace ID
   - Format: `llm-xxxxxxx`

3. **Knowledge Base ID** (`BAILIAN_KB_ID`)
   - Bailian Console → Knowledge Base → Click your KB → Copy ID
   - ~10 character alphanumeric string
   - If no KB exists: Knowledge Base → Create → Select "Document Search" → Upload documents

4. **Application ID** (`BAILIAN_APP_ID`)
   - Bailian Console → App Management → Create Agent App → Select model (recommend qwen-plus)
   - In the "Documents" section, add the knowledge base from step 3 → Save
   - Copy Application ID (32-char hex)

### Write configuration

Once all 4 IDs are collected, write them to `<SKILL_DIR>/CONFIG.md`:

```markdown
# Bailian KB Configuration

## API Key
DASHSCOPE_API_KEY=<user's API Key>

## Workspace ID
BAILIAN_WORKSPACE_ID=<user's Workspace ID>

## Knowledge Base ID
BAILIAN_KB_ID=<user's KB ID>

## Application ID
BAILIAN_APP_ID=<user's Application ID>
```

Run a test query to verify connectivity.

## Query Command

```bash
python3 <SKILL_DIR>/scripts/bailian-query.py "user's question here"
```

## Workflow

1. Receive a question about internal knowledge/documents
2. Run the query command with the user's question as argument
3. Format the returned answer (including doc references/citations) and reply

## Notes

- Ask specific questions; vague queries like "list all files" may trigger a fallback response
- Only return knowledge base results; never fabricate answers
- Preserve doc_references so users know which document the answer came from
- If errors occur, check API Key validity and account balance
- `CONFIG.md` contains sensitive credentials — **never commit to Git**
- `CONFIG.example.md` is a safe template for sharing
- Timeout is 120s (KB retrieval can be slow)

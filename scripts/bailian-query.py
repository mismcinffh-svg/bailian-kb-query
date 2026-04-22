#!/usr/bin/env python3
"""
Bailian Knowledge Base RAG Query Script
Calls a Bailian Application (with KB attached) via DashScope API.

Usage:
  python3 bailian-query.py "你的问题"

Configuration:
  Reads credentials from CONFIG.md in the skill root directory.
  If CONFIG.md doesn't exist, exits with setup instructions.
"""

import sys
import os
import json
import re
import requests
import tempfile
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(SKILL_DIR, "CONFIG.md")
CONFIG_EXAMPLE_PATH = os.path.join(SKILL_DIR, "CONFIG.example.md")


def load_config() -> dict:
    """
    Parse CONFIG.md and extract key=value pairs.
    Lines starting with # or <!-- are ignored.
    """
    if not os.path.exists(CONFIG_PATH):
        return None

    config = {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments, empty lines, HTML comments
            if not line or line.startswith("#") or line.startswith("<!--"):
                continue
            # Match KEY=VALUE pattern
            match = re.match(r"^([A-Z_]+)\s*=\s*(.+)$", line)
            if match:
                key, value = match.group(1), match.group(2).strip()
                if value and value != "your-api-key-here" and not value.startswith("your-"):
                    config[key] = value

    return config


def print_setup_instructions():
    """Print first-time setup instructions for the agent to relay to the user."""
    print(json.dumps({
        "status": "SETUP_REQUIRED",
        "message": "百煉知識庫尚未配置。需要用戶提供以下 4 個 ID 才能使用。",
        "required_fields": [
            {
                "key": "DASHSCOPE_API_KEY",
                "name": "百煉 API Key",
                "how_to_get": "登入 https://bailian.console.aliyun.com → 右上角頭像 → API Key 管理 → 複製 API Key"
            },
            {
                "key": "BAILIAN_WORKSPACE_ID",
                "name": "業務空間 ID",
                "how_to_get": "百煉 Console → 左上角業務空間下拉 → 複製空間 ID（格式：llm-xxxxxxx）"
            },
            {
                "key": "BAILIAN_KB_ID",
                "name": "知識庫 ID",
                "how_to_get": "百煉 Console → 知識庫 → 你的知識庫卡片 → 複製 ID（約 10 位字母數字）"
            },
            {
                "key": "BAILIAN_APP_ID",
                "name": "應用 ID",
                "how_to_get": "百煉 Console → 應用管理 → 創建/選擇應用（需綁定知識庫）→ 複製應用 ID（32 位 hex）"
            }
        ],
        "config_path": CONFIG_PATH,
        "next_step": "請引導用戶逐一提供以上 ID，然後將它們寫入 CONFIG.md 文件。"
    }, ensure_ascii=False, indent=2))


def query_app(question: str, api_key: str, app_id: str) -> dict:
    """
    Call Bailian Application via DashScope HTTP API.
    """
    url = f"https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "prompt": question
        },
        "parameters": {
            "has_thoughts": True,
            "doc_reference_type": "simple"
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        output = data.get("output", {})
        usage = data.get("usage", {})

        # Extract images from answer text (markdown format)
        answer_text = output.get("text", "")
        images = []
        
        # Look for markdown image syntax ![alt](url)
        import re
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(image_pattern, answer_text)
        
        for alt_text, image_url in matches:
            images.append({
                "url": image_url,
                "alt": alt_text
            })
        
        # Remove markdown images from text for cleaner output
        clean_text = re.sub(image_pattern, '', answer_text).strip()
        
        result = {
            "answer": clean_text,
            "images": images,
            "finish_reason": output.get("finish_reason", ""),
            "doc_references": output.get("doc_references", []),
            "usage": usage,
            "request_id": data.get("request_id", "")
        }
        return result

    except requests.exceptions.HTTPError as e:
        error_body = ""
        try:
            error_body = resp.text[:500]
        except:
            pass
        return {"error": str(e), "type": type(e).__name__, "detail": error_body}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


def download_image(image_url: str, temp_dir: str) -> str:
    """Download image from URL to temporary file, return file path."""
    try:
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Extract filename from URL or generate one
        filename = os.path.basename(image_url.split('?')[0])
        if not filename or '.' not in filename:
            filename = f"image_{hash(image_url) & 0xFFFFFFFF}.png"
        
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return filepath
    except Exception as e:
        print(f"Warning: Failed to download image {image_url}: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bailian-query.py \"你的问题\"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    # Load config
    config = load_config()

    if config is None:
        print_setup_instructions()
        sys.exit(2)

    # Validate required fields
    required = ["DASHSCOPE_API_KEY", "BAILIAN_APP_ID"]
    missing = [k for k in required if k not in config]
    if missing:
        print(json.dumps({
            "status": "CONFIG_INCOMPLETE",
            "message": f"CONFIG.md 缺少以下必要欄位: {', '.join(missing)}",
            "config_path": CONFIG_PATH,
            "missing_fields": missing
        }, ensure_ascii=False, indent=2))
        sys.exit(2)

    api_key = config["DASHSCOPE_API_KEY"]
    app_id = config["BAILIAN_APP_ID"]

    result = query_app(question, api_key, app_id)

    if "error" in result:
        print(json.dumps({
            "error": result["error"],
            "type": result.get("type", ""),
            "detail": result.get("detail", "")
        }, ensure_ascii=False))
        sys.exit(1)

    # Create temporary directory for downloaded images
    temp_dir = tempfile.mkdtemp(prefix="bailian_images_")
    downloaded_images = []
    
    # Download images if available
    if result.get("images"):
        for img in result["images"]:
            filepath = download_image(img["url"], temp_dir)
            if filepath:
                downloaded_images.append({
                    "path": filepath,
                    "alt": img.get("alt", "")
                })
    
    # Prepare output
    output = {
        "answer": result["answer"],
        "images": downloaded_images,
        "doc_references": result.get("doc_references", []),
        "usage": result.get("usage", {}),
        "model": result.get("usage", {}).get("models", [{}])[0].get("model_id", "unknown") if result.get("usage", {}).get("models") else "unknown",
        "temp_dir": temp_dir  # For cleanup
    }
    
    # Print JSON output for OpenClaw to parse
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


# ─── MCP Mode (JSON-RPC stdio) ────────────────────────────────────────────────

def mcp_main():
    """MCP stdio entry point: read JSON-RPC requests from stdin, write to stdout."""
    import sys
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "tools/list":
            result = {
                "tools": [{
                    "name": "bailian-kb",
                    "description": "Query Alibaba Cloud Bailian knowledge base for internal documents, company policies, HR, travel, reimbursement info.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question to ask the knowledge base"
                            }
                        },
                        "required": ["question"]
                    }
                }]
            }
            print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}, ensure_ascii=False))
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            question = arguments.get("question", "")

            if not question:
                print(json.dumps({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -1, "message": "Missing required parameter: question"}
                }, ensure_ascii=False))
                sys.stdout.flush()
                continue

            # Run the actual query
            config = load_config()
            if config is None:
                print(json.dumps({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -2, "message": "SETUP_REQUIRED: Bailian KB not configured"}
                }, ensure_ascii=False))
                sys.stdout.flush()
                continue

            api_key = config.get("DASHSCOPE_API_KEY", "")
            app_id = config.get("BAILIAN_APP_ID", "")

            if not api_key or not app_id:
                print(json.dumps({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -3, "message": f"Missing config: api_key={bool(api_key)}, app_id={bool(app_id)}"}
                }, ensure_ascii=False))
                sys.stdout.flush()
                continue

            result = query_app(question, api_key, app_id)

            if "error" in result:
                print(json.dumps({
                    "jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -4, "message": result["error"]}
                }, ensure_ascii=False))
                sys.stdout.flush()
                continue

            # Format result as MCP tool call response
            output_text = result.get("answer", "")
            doc_refs = result.get("doc_references", [])
            if doc_refs:
                refs_str = "\n".join([f"- {r.get('doc_name', r.get('title', 'Unknown'))}" for r in doc_refs])
                output_text += f"\n\n📑 引用来源:\n{refs_str}"
            
            # Add image info if available
            images = result.get("images", [])
            if images:
                output_text += "\n\n🖼️ 圖片:\n"
                for i, img in enumerate(images, 1):
                    output_text += f"  {i}. {img.get('alt', '圖片')}\n"

            print(json.dumps({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": output_text}]
                }
            }, ensure_ascii=False))
            sys.stdout.flush()

        elif method == "initialize":
            print(json.dumps({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "bailian-kb", "version": "1.0.0"}
                }
            }, ensure_ascii=False))
            sys.stdout.flush()

        elif method == "notifications/initialized":
            # Client ready signal, no response needed
            pass


if __name__ == "__main__" and len(sys.argv) == 1:
    # No args → MCP mode
    mcp_main()
elif __name__ == "__main__" and sys.argv[1] == "--mcp":
    mcp_main()

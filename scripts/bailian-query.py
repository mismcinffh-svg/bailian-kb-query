#!/usr/bin/env python3
"""
Bailian Knowledge Base RAG Query Script
Calls a Bailian Application (with KB attached) via DashScope API.
Supports step-by-step output format with images.

Usage:
  python3 bailian-query.py "你的问题"

Output format (JSON):
{
  "steps": [
    {
      "number": 1,
      "title": "Step title",
      "text": "Step description",
      "image": "/path/to/image.png"  // or null if no image
    }
  ],
  "images": [...],  // All downloaded images with paths
  "model": "qwen-max-2025-01-25",
  "temp_dir": "/tmp/..."
}
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

        result = {
            "answer": output.get("text", ""),
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


def parse_steps_with_images(answer_text: str, image_paths: list) -> list:
    """
    Parse answer text into structured steps with corresponding images.
    
    Algorithm:
    1. Split text into blocks by Step N patterns
    2. For each step, extract the markdown image that follows
    3. Return list of steps with their images
    """
    steps = []
    
    # Pattern to match Step headers
    step_pattern = r'\*\*Step\s*(\d+)[:：]\s*([^\n*]+)\*\*|\*\*(\d+)[\.\)]\s*([^\n*]+)\*\*|^(Step\s*(\d+)[:：]\s*)(.+?)(?=\n\n|\Z)|^(\d+)[\.\)]\s*([^\n]+)'
    
    # Alternative: split by numbered patterns more simply
    lines = answer_text.split('\n')
    
    current_step = None
    current_text_parts = []
    current_image_index = 0
    
    # Image pattern
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a step header
        step_match = re.match(r'^(Step\s*(\d+)[:：]\s*)(.+)', line, re.IGNORECASE)
        num_step_match = re.match(r'^(\d+)[\.\)]\s*(.+)', line)
        
        is_step_header = False
        step_num = None
        step_title = None
        
        if step_match:
            is_step_header = True
            step_title = step_match.group(3).strip()
            # Remove markdown formatting from title
            step_title = re.sub(r'\*\*(.+?)\*\*', r'\1', step_title)
            step_num = int(step_match.group(2))
        elif num_step_match:
            is_step_header = True
            step_num = int(num_step_match.group(1))
            step_title = num_step_match.group(2).strip()
            step_title = re.sub(r'\*\*(.+?)\*\*', r'\1', step_title)
        
        if is_step_header:
            # Save previous step if exists
            if current_step is not None:
                current_step['text'] = '\n'.join(current_text_parts).strip()
                # Try to find image for this step
                # Simple approach: round-robin images based on step number
                if image_paths:
                    img_idx = (current_step['number'] - 1) % len(image_paths)
                    current_step['image'] = image_paths[img_idx]
                else:
                    current_step['image'] = None
                steps.append(current_step)
            
            # Start new step
            current_step = {
                'number': step_num,
                'title': step_title,
                'text': '',
                'image': None
            }
            current_text_parts = []
        elif current_step is not None:
            # Check if this line contains an image
            img_match = re.search(img_pattern, line)
            if img_match:
                # This line has an image - skip it from text (image will be handled separately)
                # But keep the alt text if any
                alt_text = img_match.group(1)
                if alt_text and alt_text.strip():
                    current_text_parts.append(alt_text)
            else:
                # Regular text - add to step
                clean_line = re.sub(img_pattern, '', line).strip()
                if clean_line:
                    current_text_parts.append(clean_line)
    
    # Don't forget the last step
    if current_step is not None:
        current_step['text'] = '\n'.join(current_text_parts).strip()
        if image_paths:
            img_idx = (current_step['number'] - 1) % len(image_paths)
            current_step['image'] = image_paths[img_idx]
        else:
            current_step['image'] = None
        steps.append(current_step)
    
    # If no steps parsed but we have content and images, treat as single step
    if not steps and answer_text.strip() and image_paths:
        steps.append({
            'number': 1,
            'title': '',
            'text': answer_text.strip(),
            'image': image_paths[0] if image_paths else None
        })
    elif not steps:
        # Pure text only
        steps.append({
            'number': 1,
            'title': '',
            'text': answer_text.strip(),
            'image': None
        })
    
    return steps


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
    
    # Extract and download images from answer
    answer_text = result.get("answer", "")
    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    image_urls = re.findall(img_pattern, answer_text)
    
    for alt_text, image_url in image_urls:
        filepath = download_image(image_url, temp_dir)
        if filepath:
            downloaded_images.append({
                "path": filepath,
                "alt": alt_text
            })
    
    # Parse steps with images
    image_paths = [img["path"] for img in downloaded_images]
    steps = parse_steps_with_images(answer_text, image_paths)
    
    # Build response
    model_name = "unknown"
    if result.get("usage", {}).get("models"):
        model_name = result["usage"]["models"][0].get("model_id", "unknown")
    
    output = {
        "steps": steps,
        "images": downloaded_images,
        "model": model_name,
        "temp_dir": temp_dir,
        "doc_references": result.get("doc_references", [])
    }
    
    # Print JSON output
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

            # Format result as MCP tool call response (legacy format for backward compatibility)
            output_text = result.get("answer", "")
            doc_refs = result.get("doc_references", [])
            if doc_refs:
                refs_str = "\n".join([f"- {r.get('doc_name', r.get('title', 'Unknown'))}" for r in doc_refs])
                output_text += f"\n\n📑 引用來源:\n{refs_str}"

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
                    "serverInfo": {"name": "bailian-kb", "version": "2.0.0"}
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

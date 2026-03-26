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
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
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

    # Human-readable output
    print(f"📖 回答:\n{result['answer']}\n")

    # Show document references if available
    if result.get("doc_references"):
        print("📑 引用来源:")
        for ref in result["doc_references"]:
            doc_name = ref.get("doc_name", ref.get("title", "未知"))
            print(f"  - {doc_name}")

    # Show usage
    models_usage = result.get("usage", {}).get("models", [])
    if models_usage:
        total_in = sum(m.get("input_tokens", 0) for m in models_usage)
        total_out = sum(m.get("output_tokens", 0) for m in models_usage)
        model_name = models_usage[0].get("model_id", "unknown")
        print(f"\n📊 模型: {model_name} | Token: {total_in + total_out} (入:{total_in} 出:{total_out})")


if __name__ == "__main__":
    main()

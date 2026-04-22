#!/usr/bin/env python3
"""
Enhanced Bailian KB Query with Image Support
Wrapper around bailian-query.py that handles image attachments for OpenClaw.
"""

import sys
import os
import json
import subprocess
import tempfile
import shutil
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ORIGINAL_SCRIPT = os.path.join(SCRIPT_DIR, "bailian-query.py")

def run_bailian_query(question: str) -> dict:
    """Run the original bailian-query.py and return parsed JSON."""
    try:
        # Run the original script
        cmd = [sys.executable, ORIGINAL_SCRIPT, question]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=SKILL_DIR
        )
        
        if result.returncode != 0:
            print(f"Error running bailian-query.py: {result.stderr[:500]}", file=sys.stderr)
            return {"error": result.stderr[:500]}
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError as e:
            # Fallback: might be plain text output (old format)
            print(f"Warning: Could not parse JSON, falling back to text: {e}", file=sys.stderr)
            return {
                "answer": result.stdout,
                "images": [],
                "doc_references": [],
                "usage": {},
                "model": "unknown"
            }
            
    except subprocess.TimeoutExpired:
        return {"error": "Query timeout after 120 seconds"}
    except Exception as e:
        return {"error": str(e)}

def format_output_for_openclaw(result: dict) -> dict:
    """Format the result for OpenClaw consumption."""
    if "error" in result:
        return {
            "text": f"❌ 錯誤: {result['error']}",
            "images": [],
            "temp_dir": None
        }
    
    # Build text response
    text_parts = []
    
    # Add answer
    if result.get("answer"):
        text_parts.append(f"📖 回答:\n{result['answer']}\n")
    
    # Add document references
    if result.get("doc_references"):
        text_parts.append("📑 引用來源:")
        for ref in result["doc_references"]:
            doc_name = ref.get("doc_name", ref.get("title", "未知"))
            text_parts.append(f"  - {doc_name}")
        text_parts.append("")
    
    # Add usage info
    usage = result.get("usage", {})
    models = usage.get("models", [])
    if models:
        total_in = sum(m.get("input_tokens", 0) for m in models)
        total_out = sum(m.get("output_tokens", 0) for m in models)
        model_name = models[0].get("model_id", "unknown")
        text_parts.append(f"📊 模型: {model_name} | Token: {total_in + total_out} (入:{total_in} 出:{total_out})")
    
    # Prepare images
    images = []
    temp_dir = result.get("temp_dir")
    
    if result.get("images"):
        for img in result["images"]:
            if os.path.exists(img.get("path", "")):
                images.append(img["path"])
    
    return {
        "text": "\n".join(text_parts),
        "images": images,
        "temp_dir": temp_dir
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bailian-kb-enhanced.py \"你的问题\"")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print(f"🔍 查詢: {question[:100]}...")
    
    # Run query
    result = run_bailian_query(question)
    
    # Format for OpenClaw
    output = format_output_for_openclaw(result)
    
    # Print JSON for OpenClaw to parse
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
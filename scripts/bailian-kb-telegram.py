#!/usr/bin/env python3
"""
Bailian KB Telegram Integration with Image Support
This script is called by OpenClaw when the bailian-kb skill is triggered.
It handles both text and image responses for Telegram.
"""

import sys
import os
import json
import subprocess
import tempfile
import shutil
import requests

# Add skill directory to path
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_DIR)

def run_enhanced_query(question: str):
    """Run the enhanced bailian query and return formatted results."""
    enhanced_script = os.path.join(SKILL_DIR, "scripts", "bailian-kb-enhanced.py")
    
    if not os.path.exists(enhanced_script):
        # Fallback to original
        original_script = os.path.join(SKILL_DIR, "scripts", "bailian-query.py")
        cmd = [sys.executable, original_script, question]
    else:
        cmd = [sys.executable, enhanced_script, question]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=SKILL_DIR
        )
        
        if result.returncode != 0:
            return {
                "error": f"Script failed: {result.stderr[:500]}",
                "text": f"❌ 查詢失敗: {result.stderr[:200]}",
                "images": []
            }
        
        # Try to parse JSON
        try:
            data = json.loads(result.stdout)
            return data
        except json.JSONDecodeError:
            # Fallback: treat as plain text
            return {
                "text": result.stdout,
                "images": []
            }
            
    except subprocess.TimeoutExpired:
        return {
            "error": "查詢超時 (120秒)",
            "text": "❌ 查詢超時，請稍後再試",
            "images": []
        }
    except Exception as e:
        return {
            "error": str(e),
            "text": f"❌ 錯誤: {str(e)}",
            "images": []
        }

def format_for_telegram(result: dict) -> dict:
    """Format result for Telegram delivery."""
    if "error" in result and "text" not in result:
        result["text"] = f"❌ 錯誤: {result['error']}"
    
    # Ensure text field exists
    if "text" not in result:
        if "answer" in result:
            result["text"] = result["answer"]
        else:
            result["text"] = "收到回覆"
    
    # Ensure images list exists
    if "images" not in result:
        result["images"] = []
    
    return result

def main():
    if len(sys.argv) < 2:
        # No question provided, show usage
        print(json.dumps({
            "text": "請提供查詢問題，例如: /bailian \"你的問題\"",
            "images": []
        }, ensure_ascii=False))
        return
    
    question = " ".join(sys.argv[1:])
    print(f"🔍 查詢: {question}", file=sys.stderr)
    
    # Run query
    result = run_enhanced_query(question)
    
    # Format for Telegram
    formatted = format_for_telegram(result)
    
    # Print JSON for OpenClaw
    print(json.dumps(formatted, ensure_ascii=False, indent=2))
    
    # Clean up temp directory if exists
    temp_dir = result.get("temp_dir")
    if temp_dir and os.path.exists(temp_dir):
        try:
            # Only clean up if we're not keeping images for delivery
            if not result.get("images"):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    main()
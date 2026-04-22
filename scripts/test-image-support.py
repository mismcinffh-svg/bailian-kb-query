#!/usr/bin/env python3
"""
Test script to verify Bailian KB image support.
Run this to check if your knowledge base is configured for 圖文並茂回覆.
"""

import requests
import json
import re
import sys

# Configuration from CONFIG.md
CONFIG = {
    "DASHSCOPE_API_KEY": "sk-692963aa69e445f9915b195ac005978e",
    "BAILIAN_APP_ID": "808a210f72a94bfb8ac6b6f24473abbe"
}

def test_image_support(question):
    """Test if Bailian API returns images for a question."""
    url = f"https://dashscope.aliyuncs.com/api/v1/apps/{CONFIG['BAILIAN_APP_ID']}/completion"
    headers = {
        "Authorization": f"Bearer {CONFIG['DASHSCOPE_API_KEY']}",
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
    
    print(f"🔍 Testing question: {question}")
    print(f"📤 Sending request to Bailian API...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        text = data.get("output", {}).get("text", "")
        print(f"✅ Response received ({len(text)} characters)")
        
        # Check for markdown images
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, text)
        
        if images:
            print(f"🎉 SUCCESS: Found {len(images)} markdown image(s)!")
            print("\n📸 Images found:")
            for i, (alt, url) in enumerate(images, 1):
                print(f"  {i}. Alt: {alt}")
                print(f"     URL: {url[:100]}...")
            
            # Test downloading first image
            if images:
                print(f"\n🔗 Testing image download...")
                try:
                    img_response = requests.get(images[0][1], timeout=30, stream=True)
                    if img_response.status_code == 200:
                        content_type = img_response.headers.get('content-type', '')
                        content_length = img_response.headers.get('content-length', '0')
                        print(f"✅ Image download successful:")
                        print(f"   Content-Type: {content_type}")
                        print(f"   Size: {content_length} bytes")
                    else:
                        print(f"⚠️  Image download failed: HTTP {img_response.status_code}")
                except Exception as e:
                    print(f"⚠️  Image download test failed: {e}")
        else:
            print(f"❌ No markdown images found in response.")
            print("\n🔍 Checking response content...")
            # Look for any image indicators
            if "![" in text or "](" in text:
                print("   Found partial markdown syntax but no complete images")
            if "http" in text and ("png" in text or "jpg" in text or "jpeg" in text):
                print("   Found potential image URLs in text")
            
            print("\n💡 Suggestions:")
            print("   1. Check knowledge base configuration: 使用場景 should be '圖文並茂回覆'")
            print("   2. Ensure application uses 千問-Plus or 千問-Plus-Latest model")
            print("   3. Verify documents contain embedded images")
            print("   4. Try more specific questions about document content")
        
        # Show document references
        doc_refs = data.get("output", {}).get("doc_references", [])
        if doc_refs:
            print(f"\n📑 Document references:")
            for ref in doc_refs:
                doc_name = ref.get("doc_name", ref.get("title", "Unknown"))
                print(f"   - {doc_name}")
        
        return len(images) > 0
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout (60 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    # Test questions
    test_questions = [
        "請展示供應鏈系統的界面截圖",
        "Forward Fashion New Supply Chain Functional Specification 文件中有哪些界面截圖？",
        "Shipment Notice Header 界面是什麼樣子？",
        "Goods Receiving Note Detail 界面截圖",
        "測試圖片顯示功能"
    ]
    
    print("=" * 60)
    print("Bailian KB Image Support Test")
    print("=" * 60)
    print(f"App ID: {CONFIG['BAILIAN_APP_ID']}")
    print(f"API Key: {CONFIG['DASHSCOPE_API_KEY'][:10]}...")
    print("=" * 60)
    
    success_count = 0
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*40}")
        print(f"Test {i}/{len(test_questions)}")
        print(f"{'='*40}")
        
        if test_image_support(question):
            success_count += 1
        
        if i < len(test_questions):
            input("\nPress Enter to continue to next test...")
    
    print(f"\n{'='*60}")
    print(f"Test Summary: {success_count}/{len(test_questions)} questions returned images")
    print(f"{'='*60}")
    
    if success_count > 0:
        print("✅ Image support is WORKING!")
        print("\nNext steps:")
        print("   1. Use bailian-kb-enhanced.py for image downloads")
        print("   2. Configure OpenClaw to send images as attachments")
    else:
        print("❌ No images returned in any test")
        print("\nTroubleshooting:")
        print("   1. Login to https://bailian.console.aliyun.com")
        print("   2. Check knowledge base → 使用場景 should be '圖文並茂回覆'")
        print("   3. Check application → Model should be 千問-Plus/Plus-Latest")
        print("   4. Verify documents contain actual images")
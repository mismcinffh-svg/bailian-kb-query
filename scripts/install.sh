#!/bin/bash
# Bailian KB Query — Setup Script
# Run this once to install the skill AND register the MCP tool.
#
# Usage: bash install.sh
#
# What it does:
#  1. Checks python3 and mcporter are available
#  2. Registers bailian-kb as an MCP tool via mcporter
#  3. Prints next steps for CONFIG.md setup

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Bailian KB Query — Installation"
echo "================================="

# Check python3
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3 first."
    exit 1
fi
echo "✅ python3 found"

# Check mcporter
if ! command -v mcporter &> /dev/null; then
    echo "⚠️  mcporter not found — MCP tool registration will be skipped."
    echo "   Install with: npm i -g mcporter"
else
    echo "✅ mcporter found — registering MCP tool..."
    mcporter config add bailian-kb --stdio "python3 $SCRIPT_DIR/bailian-query.py --mcp" 2>&1
    echo "✅ bailian-kb MCP tool registered"
fi

# Copy CONFIG.example to CONFIG if CONFIG.md doesn't exist
if [ ! -f "$SKILL_DIR/CONFIG.md" ]; then
    cp "$SKILL_DIR/CONFIG.example.md" "$SKILL_DIR/CONFIG.md"
    echo "✅ Created CONFIG.md from CONFIG.example.md"
    echo ""
    echo "📝 Next step: Edit CONFIG.md and add your 4 Bailian credentials:"
    echo "   - DASHSCOPE_API_KEY"
    echo "   - BAILIAN_WORKSPACE_ID"
    echo "   - BAILIAN_KB_ID"
    echo "   - BAILIAN_APP_ID"
else
    echo "✅ CONFIG.md already exists"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Test with:"
echo "  mcporter call bailian-kb.bailian-kb question=\"測試\""

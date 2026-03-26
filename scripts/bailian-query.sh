#!/bin/bash
# Wrapper script for bailian-query.py
# Usage: bailian-query.sh "你的问题"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/bailian-query.py" "$@"

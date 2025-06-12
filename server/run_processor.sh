#!/bin/bash
# Load environment variables and run process_english_tasks.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
set -a
if [ -f "$SCRIPT_DIR/.env" ]; then
  source "$SCRIPT_DIR/.env"
fi
set +a
cd "$SCRIPT_DIR" || exit 1
python3 process_english_tasks.py >> "$SCRIPT_DIR/english_tasks.log" 2>&1

#!/bin/bash

# Script to run process_english_tasks.py every 30 seconds

echo "Starting Things3 Server Process Monitor"
echo "======================================="
echo ""
echo "This will run process_english_tasks.py every 30 seconds."
echo "Press Ctrl+C to stop."
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if process_english_tasks.py exists
if [ ! -f "process_english_tasks.py" ]; then
    echo "Error: process_english_tasks.py not found!"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Please create a .env file with your OPENAI_API_KEY"
    echo "Example:"
    echo "  OPENAI_API_KEY=your-key-here"
    exit 1
fi

# Check if credentials exist
if [ ! -f "secrets/credentials.json" ]; then
    echo "Error: secrets/credentials.json not found!"
    echo "Please copy your Google credentials to server/secrets/"
    exit 1
fi

# Load environment variables from .env
export $(cat .env | grep -v '^#' | xargs)

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
fi

# Main loop
while true; do
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running process_english_tasks.py..."
    echo "-----------------------------------------------------------"
    
    python3 process_english_tasks.py
    
    echo ""
    echo "Waiting 30 seconds before next run..."
    sleep 30
done 
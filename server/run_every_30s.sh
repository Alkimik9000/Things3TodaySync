#!/bin/bash

# Script to run process_english_tasks.py and create_things_links.py every 30 seconds

echo "Starting Things3 Server Process Monitor"
echo "======================================="
echo ""
echo "This will run process_english_tasks.py and create_things_links.py every 30 seconds."
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

# Check if Flask server is running
FLASK_PID=$(pgrep -f "serve_urls.py")
if [ -z "$FLASK_PID" ]; then
    echo "Starting Flask URL server in background..."
    export THINGS_API_KEY=${THINGS_API_KEY:-"default-api-key"}
    export FLASK_PORT=${FLASK_PORT:-5000}
    export FLASK_HOST=${FLASK_HOST:-"0.0.0.0"}
    nohup python3 apple_shortcuts/serve_urls.py > flask_server.log 2>&1 &
    echo "Flask server started on port $FLASK_PORT"
    sleep 2  # Give server time to start
else
    echo "Flask server already running (PID: $FLASK_PID)"
fi

# Main loop
while true; do
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running process_english_tasks.py..."
    echo "-----------------------------------------------------------"
    
    python3 process_english_tasks.py
    
    echo ""
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running create_things_links.py..."
    echo "-----------------------------------------------------------"
    
    python3 apple_shortcuts/create_things_links.py
    
    echo ""
    echo "Waiting 30 seconds before next run..."
    sleep 30
done 
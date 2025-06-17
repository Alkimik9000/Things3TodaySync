#!/bin/bash

echo "=== Things3 Server Process Setup ==="
echo ""
echo "This script will help you set up the server process to run every 30 seconds."
echo ""

# Check if we're in the server directory
if [ ! -f "process_english_tasks.py" ]; then
    echo "Error: Please run this script from the server directory"
    exit 1
fi

echo "Step 1: Environment Setup"
echo "========================="
echo ""
echo "You need to create a .env file in the server directory with the following variables:"
echo ""
echo "OPENAI_API_KEY=\"your-openai-api-key\""
echo "EC2_HOST=\"your-ec2-host\" (optional, for uploading to EC2)"
echo "EC2_USER=\"ubuntu\" (optional, default is ubuntu)"
echo "EC2_KEY_PATH=\"/path/to/key.pem\" (optional, for EC2 upload)"
echo "REMOTE_FETCHED_CSV=\"/path/on/server/fetched_tasks.csv\" (optional)"
echo "REMOTE_PROCESSED_CSV=\"/path/on/server/processed_tasks.csv\" (optional)"
echo ""
echo "Press Enter when you've created the .env file..."
read

echo ""
echo "Step 2: Google Authentication"
echo "============================="
echo ""
echo "You need to set up Google credentials:"
echo "1. Go to https://console.cloud.google.com/"
echo "2. Create a new project or select existing"
echo "3. Enable Google Tasks API"
echo "4. Create credentials (OAuth 2.0 Client ID)"
echo "5. Download the credentials as 'credentials.json'"
echo "6. Place it in ../secrets/credentials.json"
echo ""
echo "Press Enter when you've set up Google credentials..."
read

echo ""
echo "Step 3: Running the Process"
echo "==========================="
echo ""
echo "You have several options to run this every 30 seconds:"
echo ""
echo "Option 1: Simple loop (run in terminal):"
echo "-----------------------------------------"
echo "while true; do"
echo "    python3 process_english_tasks.py"
echo "    sleep 30"
echo "done"
echo ""
echo "Option 2: Using watch command:"
echo "------------------------------"
echo "watch -n 30 python3 process_english_tasks.py"
echo ""
echo "Option 3: Create a LaunchAgent (macOS) for automatic startup:"
echo "-------------------------------------------------------------"
echo "Create ~/Library/LaunchAgents/com.things3.server_processor.plist"
echo ""
echo "Option 4: Run on EC2 with cron:"
echo "--------------------------------"
echo "Add to crontab on EC2:"
echo "* * * * * cd /path/to/server && python3 process_english_tasks.py"
echo "* * * * * sleep 30 && cd /path/to/server && python3 process_english_tasks.py"
echo ""

# Test if environment is set up
if [ -f ".env" ]; then
    echo "Found .env file ✓"
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "Warning: OPENAI_API_KEY is not set in .env"
    else
        echo "OPENAI_API_KEY is set ✓"
    fi
else
    echo "Warning: .env file not found"
fi

if [ -f "../secrets/credentials.json" ]; then
    echo "Found Google credentials ✓"
else
    echo "Warning: Google credentials not found at ../secrets/credentials.json"
fi

echo ""
echo "Would you like to test the script now? (y/n)"
read answer

if [ "$answer" = "y" ]; then
    echo "Running process_english_tasks.py..."
    python3 process_english_tasks.py
fi 
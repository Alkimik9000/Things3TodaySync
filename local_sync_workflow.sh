#!/bin/bash
# Local sync workflow - runs entirely on macOS without server

set -e

# Change to script directory
cd "$(dirname "$0")"

# Load configuration
if [ ! -f "config.sh" ]; then
    echo "Error: config.sh not found. Please run setup.sh first."
    exit 1
fi
source config.sh

# Log file
LOG_FILE="outputs/local_sync_workflow.log"
mkdir -p outputs

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check requirements
check_requirements() {
    # Check for Things3 auth token
    if [ -z "$THINGS_AUTH_TOKEN" ]; then
        log "ERROR: THINGS_AUTH_TOKEN not set. Please set it in your environment."
        exit 1
    fi
    
    # Check for OpenAI API key (if using English task processing)
    if [ -z "$OPENAI_API_KEY" ]; then
        log "WARNING: OPENAI_API_KEY not set. English task processing will be skipped."
    fi
    
    # Check for Google credentials
    if [ ! -f "secrets/credentials.json" ]; then
        log "ERROR: Google credentials not found. Please set up Google Tasks API."
        exit 1
    fi
}

main() {
    log "========================================="
    log "Starting Local Sync Workflow"
    log "========================================="
    
    # Check requirements
    check_requirements
    
    # Step 1: Extract tasks from Things3
    log "Step 1: Extracting tasks from Things3..."
    python3 extract_tasks.py >> "$LOG_FILE" 2>&1
    
    if [ "$GOOGLE_TASKS_SYNC" = "1" ]; then
        # Extract all lists
        python3 extract_upcoming.py >> "$LOG_FILE" 2>&1
        python3 extract_anytime.py >> "$LOG_FILE" 2>&1
        python3 extract_someday.py >> "$LOG_FILE" 2>&1
    fi
    
    # Step 2: Sync from Things3 to Google Tasks
    log "Step 2: Syncing Things3 to Google Tasks..."
    if [ "$GOOGLE_TASKS_SYNC" = "1" ]; then
        python3 import_google_tasks.py --all >> "$LOG_FILE" 2>&1
    else
        python3 import_google_tasks.py >> "$LOG_FILE" 2>&1
    fi
    
    # Step 3: Two-way sync (Google Tasks changes back to Things3)
    log "Step 3: Two-way sync (Google → Things3)..."
    python3 google_to_things_sync.py >> "$LOG_FILE" 2>&1
    
    # Step 4: Process English tasks (if OpenAI key is available)
    if [ -n "$OPENAI_API_KEY" ]; then
        log "Step 4: Processing English tasks..."
        python3 local_process_and_sync.py >> "$LOG_FILE" 2>&1
    else
        log "Step 4: Skipping English task processing (no OpenAI key)"
    fi
    
    log "========================================="
    log "Local sync workflow completed"
    log "========================================="
}

# Run main function
main 
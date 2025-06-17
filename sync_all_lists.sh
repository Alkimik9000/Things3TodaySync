#!/bin/bash

# Sync all Things3 lists to Google Tasks
# This script extracts tasks from all Things3 lists and syncs them to separate Google Tasks lists

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/outputs/things_sync.log"

# Create outputs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/outputs"

# Log function
log() {
    local level="${1:-INFO}"
    local message="${2:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log "INFO" "Starting full Things3 sync..."
START_TIME=$(date +%s)

# Change to script directory
cd "$SCRIPT_DIR"

# Source configuration if it exists
if [ -f "config.sh" ]; then
    source config.sh
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Extract tasks from each list
log "INFO" "Extracting Today tasks from Things3..."
if python3 extract_tasks.py; then
    TODAY_COUNT=$(($(wc -l < outputs/today_view.csv 2>/dev/null || echo 1) - 1))
    log "INFO" "Extracted $TODAY_COUNT Today tasks"
else
    log "ERROR" "Failed to extract Today tasks"
    exit 1
fi

log "INFO" "Extracting Upcoming tasks from Things3..."
if python3 extract_upcoming.py; then
    UPCOMING_COUNT=$(($(wc -l < outputs/upcoming_tasks.csv 2>/dev/null || echo 1) - 1))
    log "INFO" "Extracted $UPCOMING_COUNT Upcoming tasks"
else
    log "ERROR" "Failed to extract Upcoming tasks"
    exit 1
fi

log "INFO" "Extracting Anytime tasks from Things3..."
if python3 extract_anytime.py; then
    ANYTIME_COUNT=$(($(wc -l < outputs/anytime_tasks.csv 2>/dev/null || echo 1) - 1))
    log "INFO" "Extracted $ANYTIME_COUNT Anytime tasks"
else
    log "ERROR" "Failed to extract Anytime tasks"
    exit 1
fi

# Import all lists to Google Tasks
log "INFO" "Syncing all lists with Google Tasks..."
if python3 import_google_tasks.py --all; then
    log "SUCCESS" "✅ Google Tasks sync completed successfully"
else
    log "ERROR" "❌ Google Tasks sync failed"
    exit 1
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log "INFO" "Full sync completed in $DURATION seconds"
log "INFO" "Total tasks: Today=$TODAY_COUNT, Upcoming=$UPCOMING_COUNT, Anytime=$ANYTIME_COUNT" 
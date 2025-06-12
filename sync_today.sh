#!/bin/bash

# Things3 Today View to Google Tasks Sync
# -------------------------------------
# This script:
# 1. Extracts Today's tasks from Things3
# 2. Saves a local backup of the tasks
# 3. Syncs with Google Tasks
# 4. Runs every 10 minutes via launchd

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.sh"
LOG_FILE="$SCRIPT_DIR/sync.log"

# Load configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ❌ Error: Configuration file not found: $CONFIG_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# Source the configuration
. "$CONFIG_FILE"

# Activate Python virtual environment if present
if [ -d "$SCRIPT_DIR/venv" ]; then
    # shellcheck source=/dev/null
    . "$SCRIPT_DIR/venv/bin/activate"
fi

# Log function
log() {
    local level="${1:-INFO}"
    local message="${2:-}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Remove the level from the message if it was passed as first argument
    if [ "$1" = "-i" ] || [ "$1" = "-w" ] || [ "$1" = "-e" ] || [ "$1" = "-s" ]; then
        level="${1#-}"
        message="${@:2}"
    fi
    
    # Map short level names to full names
    case "$level" in
        i) level="INFO" ;;
        w) level="WARN" ;;
        e) level="ERROR" ;;
        s) level="SUCCESS" ;;
    esac
    
    # Log to file
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Main sync function
sync_today_view() {
    local start_time=$(date +%s)
    log -i "Starting Today view sync..."
    
    # Step 1: Extract tasks from Things3
    log -i "Extracting tasks from Things3..."
    if ! python3 "$EXTRACT_SCRIPT"; then
        log -e "Failed to extract Today view from Things3"
        return 1
    fi
    
    # Verify the CSV was created
    if [ ! -f "$LOCAL_CSV" ]; then
        log -e "Today view CSV was not created by extractor script"
        return 1
    fi
    
    local task_count=$(($(wc -l < "$LOCAL_CSV") - 1))  # Subtract header
    log -i "Extracted $task_count tasks to $LOCAL_CSV"
    
    # Step 2: Sync with Google Tasks if enabled
    if [ -n "$GOOGLE_TASKS_SYNC" ] && [ "$GOOGLE_TASKS_SYNC" = "1" ]; then
        log -i "Syncing with Google Tasks..."
        if python3 "$SCRIPT_DIR/import_google_tasks.py" >> "$LOG_FILE" 2>&1; then
            log -s "✅ Google Tasks sync completed successfully"
        else
            log -w "⚠️  Google Tasks sync encountered errors"
        fi
    fi
    
    # Calculate and log sync duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log -i "Sync completed in ${duration} seconds"
    
    # Add a separator for better log readability
    echo "--------------------------------------------------" >> "$LOG_FILE"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Run the sync
sync_today_view

exit 0

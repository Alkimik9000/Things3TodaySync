#!/bin/bash

# Things3 Today View Sync Script
# ----------------------------
# 1. Extracts Today's tasks from Things3
# 2. Syncs the Today view to a remote server
# 3. Maintains proper logging and error handling

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.sh"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Configuration file not found: $CONFIG_FILE"
    echo "Please copy config.sh.example to config.sh and update it with your settings"
    exit 1
fi

# Source the configuration
. "$CONFIG_FILE"

# Activate Python virtual environment if present
if [ -d "$SCRIPT_DIR/venv" ]; then
    # shellcheck source=/dev/null
    . "$SCRIPT_DIR/venv/bin/activate"
fi

# Verify required variables are set
if [ -z "$THINGS_DB" ] || [ -z "$EC2_HOST" ] || [ -z "$EC2_KEY_PATH" ]; then
    echo "❌ Error: Required configuration variables not set in $CONFIG_FILE"
    exit 1
fi

# Log file location is set in config.sh
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
    
    # Color codes for terminal output
    local color_reset='\033[0m'
    local color_red='\033[0;31m'
    local color_green='\033[0;32m'
    local color_yellow='\033[1;33m'
    local color_blue='\033[0;34m'
    
    # Set color based on log level
    local color="$color_blue"
    case "$level" in
        "ERROR") color="$color_red" ;;
        "SUCCESS") color="$color_green" ;;
        "WARN") color="$color_yellow" ;;
    esac
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Also print to terminal if running interactively
    if [ -t 1 ]; then
        echo -e "${color}[$timestamp] [$level] $message${color_reset}"
    fi
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to test SSH connection
test_ssh_connection() {
    if ! ssh -q -i "$EC2_KEY_PATH" -o BatchMode=yes -o ConnectTimeout=5 "$EC2_USER@$EC2_HOST" exit; then
        log -e "Cannot connect to $EC2_USER@$EC2_HOST using key $EC2_KEY_PATH"
        return 1
    fi
    return 0
}

# Function to sync Today view
sync_today_view() {
    log -i "Starting Today view sync..."
    
    # Extract tasks
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
    
    # Optionally sync tasks with Google Tasks
    if [ -n "$GOOGLE_TASKS_SYNC" ] && [ "$GOOGLE_TASKS_SYNC" = "1" ]; then
        if python3 "$SCRIPT_DIR/import_google_tasks.py" >> "$LOG_FILE" 2>&1; then
            log -s "Google Tasks sync completed"
        else
            log -w "Google Tasks sync encountered errors"
        fi
    fi

    # Upload to EC2
    log -i "Uploading to EC2..."
    if scp -i "$EC2_KEY_PATH" "$LOCAL_CSV" "$EC2_USER@$EC2_HOST:$REMOTE_CSV" >/dev/null 2>&1; then
        log -s "Successfully uploaded $LOCAL_CSV to EC2 ($task_count tasks)"
        return 0
    else
        log -e "Failed to upload $LOCAL_CSV to EC2"
        return 1
    fi
}

# Main loop
log -s "🚀 Starting Things3 Today View sync service"
log -i "Syncing Today view every 60 seconds"

# Calculate the sleep time to align with the minute boundary
calculate_sleep_time() {
    local current_seconds=$(date +%s)
    local next_minute=$(( (current_seconds / 60 + 1) * 60 ))
    echo $((next_minute - current_seconds))
}

# Initial sleep to align with the minute boundary
initial_sleep=$(calculate_sleep_time)
log -i "Initial sleep for ${initial_sleep}s to align with minute boundary"
sleep "$initial_sleep"

while true; do
    sync_start_time=$(date +%s)
    
    # Log the sync start
    log -i "--- Starting sync at $(date) ---"
    
    # Sync the Today view
    if sync_today_view; then
        log -s "✅ Today view sync completed successfully"
    else
        log -e "❌ Today view sync failed, will retry on next cycle"
    fi
    
    # Calculate remaining time until next minute
    current_time=$(date +%s)
    time_elapsed=$((current_time - sync_start_time))
    sleep_time=$((60 - time_elapsed % 60))
    
    # Ensure we don't sleep for a negative time
    if [ $sleep_time -gt 0 ]; then
        log -i "Sync completed in ${time_elapsed}s. Next sync in ${sleep_time}s..."
        sleep $sleep_time
    else
        log -w "Sync took too long (${time_elapsed}s), starting next cycle immediately"
    fi
done
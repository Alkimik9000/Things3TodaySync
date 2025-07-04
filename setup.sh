#!/bin/bash

# Setup script for Things3 to Google Tasks Sync
# This script helps users configure the local sync script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_BACKUP_DIR="$HOME/ThingsBackups"
DEFAULT_THINGS_DB="$HOME/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/ThingsData-BQ2NY/Things Database.thingsdatabase/main.sqlite"
DEFAULT_GOOGLE_TASKS_SYNC="1"

# Check for existing config
if [ -f "config.sh" ]; then
    # Source config to get existing values
    # shellcheck source=/dev/null
    . config.sh
    echo -e "${YELLOW}Found existing configuration. Current settings:${NC}"
    echo -e "Things3 Database: ${BLUE}${THINGS_DB:-$DEFAULT_THINGS_DB}${NC}"
    echo -e "Backup Directory: ${BLUE}${BACKUP_DIR:-$DEFAULT_BACKUP_DIR}${NC}"
    echo -e "Google Tasks Sync: ${BLUE}${GOOGLE_TASKS_SYNC:-$DEFAULT_GOOGLE_TASKS_SYNC}${NC}\n"
    
    read -p "Do you want to update these settings? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Keeping existing configuration.${NC}"
        exit 0
    fi
    
    # Use existing values as defaults
    default_things_db="${THINGS_DB:-$DEFAULT_THINGS_DB}"
    default_backup_dir="${BACKUP_DIR:-$DEFAULT_BACKUP_DIR}"
    default_google_tasks_sync="${GOOGLE_TASKS_SYNC:-$DEFAULT_GOOGLE_TASKS_SYNC}"
else
    # Default values for new setup
    default_things_db="$DEFAULT_THINGS_DB"
    default_backup_dir="$DEFAULT_BACKUP_DIR"
    default_google_tasks_sync="$DEFAULT_GOOGLE_TASKS_SYNC"
fi

echo -e "${YELLOW}=== Things3 to Google Tasks Sync Setup ===${NC}\n"

# Get user input
echo -e "${GREEN}Local Configuration:${NC}"

read -p "Path to Things3 database [${BLUE}${default_things_db}${NC}]: " things_db
things_db="${things_db:-$default_things_db}"

read -p "Backup directory [${BLUE}${default_backup_dir}${NC}]: " backup_dir
backup_dir="${backup_dir:-$default_backup_dir}"

read -p "Enable Google Tasks sync (1=yes, 0=no) [${BLUE}${default_google_tasks_sync}${NC}]: " google_tasks_sync
google_tasks_sync="${google_tasks_sync:-$default_google_tasks_sync}"

# Create backup of existing config if it exists
if [ -f "config.sh" ]; then
    backup_name="config.sh.backup.$(date +%Y%m%d_%H%M%S)"
    cp config.sh "$backup_name"
    echo -e "${YELLOW}Backed up existing config to $backup_name${NC}"
fi

# Create config file
cat > config.sh <<EOL
#!/bin/bash

# Configuration for Things3 to Google Tasks Sync
# This file contains sensitive information - DO NOT COMMIT TO VERSION CONTROL
# Generated by setup.sh on $(date)

# ===== LOCAL SETTINGS =====

# Path to Things3 database (default for macOS)
THINGS_DB="${things_db}"

# Local directories
BACKUP_DIR="${backup_dir}"  # Local directory for database backups
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"  # Directory of this script
LOG_FILE="\$SCRIPT_DIR/sync.log"  # Log file location

# ===== SYNC SETTINGS =====

# File names (usually don't need to change)
LOCAL_CSV="outputs/today_view.csv"
EXTRACT_SCRIPT="extract_tasks.py"  # Python script to extract tasks from Things3

# Google Tasks Sync (1=enabled, 0=disabled)
GOOGLE_TASKS_SYNC="${google_tasks_sync}"

# ===== EXPORT VARIABLES =====
# (Don't modify these directly)
export THINGS_DB BACKUP_DIR LOCAL_CSV EXTRACT_SCRIPT SCRIPT_DIR LOG_FILE GOOGLE_TASKS_SYNC
EOL

# Make config file executable
chmod +x config.sh

# Create necessary directories
mkdir -p "$backup_dir" outputs secrets

# Set secure permissions
chmod 700 "$backup_dir"

# Create archive directory if it doesn't exist
mkdir -p archive

echo -e "\n${GREEN}✓ Configuration saved to config.sh${NC}"

# Google OAuth setup
if [ "$google_tasks_sync" = "1" ]; then
    echo -e "\n${YELLOW}Google Tasks Setup:${NC}"
    echo "1. Go to https://console.cloud.google.com/"
    echo "2. Create a new project"
    echo "3. Enable the Google Tasks API"
    echo "4. Create OAuth 2.0 credentials (Desktop app)"
    echo "5. Download the credentials and save as 'secrets/credentials.json' in this directory"
    echo -e "\nAfter saving credentials.json, run: ${BLUE}./sync_today.sh${NC} to complete OAuth setup"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Review the configuration in config.sh"
echo "2. Make sure the sync script is executable:"
echo "   ${BLUE}chmod +x sync_today.sh${NC}"
echo "3. Test the sync manually (this will also set up Google OAuth if enabled):"
echo "   ${BLUE}./sync_today.sh${NC}"
echo "4. (Optional) Install the launch agent for automatic startup:"
echo "   ${BLUE}cp com.things3.today_sync.plist ~/Library/LaunchAgents/${NC}"
echo "   ${BLUE}launchctl load ~/Library/LaunchAgents/com.things3.today_sync.plist${NC}"

echo -e "\n${GREEN}✓ Setup complete!${NC}"

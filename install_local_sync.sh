#!/bin/bash
# Install local sync workflow as LaunchAgent

set -e

# Get the absolute path of the current directory
WORKING_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing Local Sync Workflow..."
echo "Working directory: $WORKING_DIR"

# Make scripts executable
chmod +x local_sync_workflow.sh

# Update the plist file with the correct working directory
sed "s|__WORKING_DIRECTORY__|$WORKING_DIR|g" com.things3.local_sync.plist > ~/Library/LaunchAgents/com.things3.local_sync.plist

# Update the ProgramArguments to use the correct script path
/usr/libexec/PlistBuddy -c "Set :ProgramArguments:1 $WORKING_DIR/local_sync_workflow.sh" ~/Library/LaunchAgents/com.things3.local_sync.plist

# Load the launch agent
launchctl unload ~/Library/LaunchAgents/com.things3.local_sync.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.things3.local_sync.plist

echo "✓ Local sync workflow installed successfully!"
echo ""
echo "The sync will run every 30 minutes."
echo "To check status: launchctl list | grep com.things3.local_sync"
echo "To view logs: tail -f outputs/local_sync_workflow.log"
echo ""
echo "To uninstall: launchctl unload ~/Library/LaunchAgents/com.things3.local_sync.plist" 
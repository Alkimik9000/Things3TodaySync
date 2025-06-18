#!/bin/bash

# Install script for macOS launchd service

echo "Installing Google Tasks Interceptor service for macOS..."

# Get the absolute path to the project
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SERVICE_FILE="$PROJECT_DIR/server/services/com.things3.google-tasks-interceptor.plist"
INSTALL_PATH="$HOME/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist"

# Update paths in the plist file
sed -i '' "s|/Users/markofir/Development/Things3-Android-Companion-App-Detailed|$PROJECT_DIR|g" "$SERVICE_FILE"

# Create logs directory
mkdir -p "$PROJECT_DIR/server/logs"

# Copy service file to LaunchAgents
cp "$SERVICE_FILE" "$INSTALL_PATH"

# Load the service
launchctl load "$INSTALL_PATH"

# Check if service is running
if launchctl list | grep -q "com.things3.google-tasks-interceptor"; then
    echo "✅ Service installed and loaded successfully!"
    echo ""
    echo "Service name: com.things3.google-tasks-interceptor"
    echo "Logs: $PROJECT_DIR/server/logs/"
    echo ""
    echo "Useful commands:"
    echo "  View status:  launchctl list | grep google-tasks-interceptor"
    echo "  Stop service: launchctl unload $INSTALL_PATH"
    echo "  Start service: launchctl load $INSTALL_PATH"
    echo "  View logs: tail -f $PROJECT_DIR/server/logs/google-tasks-interceptor.log"
else
    echo "❌ Failed to load service"
    exit 1
fi 
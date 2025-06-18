#!/bin/bash

# Install script for Ubuntu systemd service

echo "Installing Google Tasks Interceptor service for Ubuntu..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./install_ubuntu.sh"
    exit 1
fi

# Get the project directory (assuming standard path)
PROJECT_DIR="/home/ubuntu/Things3-Android-Companion-App-Detailed"
SERVICE_FILE="$PROJECT_DIR/server/services/google-tasks-interceptor.service"
INSTALL_PATH="/etc/systemd/system/google-tasks-interceptor.service"

# Create logs directory
mkdir -p "$PROJECT_DIR/server/logs"
chown ubuntu:ubuntu "$PROJECT_DIR/server/logs"

# Copy service file to systemd
cp "$SERVICE_FILE" "$INSTALL_PATH"

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
systemctl enable google-tasks-interceptor.service
systemctl start google-tasks-interceptor.service

# Check if service is running
if systemctl is-active --quiet google-tasks-interceptor.service; then
    echo "✅ Service installed and started successfully!"
    echo ""
    echo "Service name: google-tasks-interceptor"
    echo "Logs: $PROJECT_DIR/server/logs/"
    echo ""
    echo "Useful commands:"
    echo "  View status:  sudo systemctl status google-tasks-interceptor"
    echo "  Stop service: sudo systemctl stop google-tasks-interceptor"
    echo "  Start service: sudo systemctl start google-tasks-interceptor"
    echo "  View logs: sudo journalctl -u google-tasks-interceptor -f"
    echo "  View app logs: tail -f $PROJECT_DIR/server/logs/google-tasks-interceptor.log"
else
    echo "❌ Failed to start service"
    systemctl status google-tasks-interceptor.service
    exit 1
fi 
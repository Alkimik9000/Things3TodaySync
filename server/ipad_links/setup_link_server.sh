#!/bin/bash
# Install a systemd service to run serve_things_links.py on boot.
# Usage: sudo ./setup_link_server.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="things-links"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<SERVICE | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Things links HTTP server
After=network.target

[Service]
ExecStart=/usr/bin/python3 $SCRIPT_DIR/serve_things_links.py
WorkingDirectory=$SCRIPT_DIR
Restart=always
User=$(whoami)
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME.service"

echo "Service installed. Check status with: sudo systemctl status $SERVICE_NAME.service"

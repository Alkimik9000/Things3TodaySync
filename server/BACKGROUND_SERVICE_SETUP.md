# Background Service Setup Guide

This guide explains how to set up the Google Tasks Interceptor as a background service on macOS and Ubuntu.

## Overview

The `google-tasks-interceptor` service runs `automated_workflow.py` continuously in the background, checking for new English tasks in Google Tasks every 30 seconds.

## macOS Setup (launchd)

### Installation

1. Navigate to the server directory:
   ```bash
   cd server
   ```

2. Run the installation script:
   ```bash
   ./services/install_macos.sh
   ```

### Manual Installation

If you prefer manual installation:

1. Copy the plist file:
   ```bash
   cp services/com.things3.google-tasks-interceptor.plist ~/Library/LaunchAgents/
   ```

2. Load the service:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist
   ```

### Management Commands

- **Check status**: `launchctl list | grep google-tasks-interceptor`
- **Stop service**: `launchctl unload ~/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist`
- **Start service**: `launchctl load ~/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist`
- **View logs**: `tail -f server/logs/google-tasks-interceptor.log`
- **Remove service**: 
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist
  rm ~/Library/LaunchAgents/com.things3.google-tasks-interceptor.plist
  ```

## Ubuntu Setup (systemd)

### Prerequisites

1. Ensure the project is cloned to `/home/ubuntu/Things3-Android-Companion-App-Detailed`
2. Virtual environment is set up with all dependencies installed
3. `.env` file exists with required environment variables

### Installation

1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-host
   ```

2. Navigate to the server directory:
   ```bash
   cd /home/ubuntu/Things3-Android-Companion-App-Detailed/server
   ```

3. Run the installation script:
   ```bash
   sudo ./services/install_ubuntu.sh
   ```

### Manual Installation

If you prefer manual installation:

1. Copy the service file:
   ```bash
   sudo cp services/google-tasks-interceptor.service /etc/systemd/system/
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable google-tasks-interceptor
   sudo systemctl start google-tasks-interceptor
   ```

### Management Commands

- **Check status**: `sudo systemctl status google-tasks-interceptor`
- **Stop service**: `sudo systemctl stop google-tasks-interceptor`
- **Start service**: `sudo systemctl start google-tasks-interceptor`
- **Restart service**: `sudo systemctl restart google-tasks-interceptor`
- **View logs**: `sudo journalctl -u google-tasks-interceptor -f`
- **View app logs**: `tail -f /home/ubuntu/Things3-Android-Companion-App-Detailed/server/logs/google-tasks-interceptor.log`
- **Disable service**: `sudo systemctl disable google-tasks-interceptor`

## Verification

After installation, verify the service is working:

1. Add a test English task to Google Tasks:
   ```bash
   python server/add_test_task.py
   ```

2. Monitor the logs to see it being processed:
   - macOS: `tail -f server/logs/google-tasks-interceptor.log`
   - Ubuntu: `sudo journalctl -u google-tasks-interceptor -f`

3. Check that:
   - Task is detected within 30 seconds
   - Task is translated to Hebrew with emojis
   - Things3 URL is generated (and opened on macOS)
   - Original task is deleted from Google Tasks

## Troubleshooting

### Service Not Starting

1. Check logs for errors:
   - macOS: `tail -f server/logs/google-tasks-interceptor.error.log`
   - Ubuntu: `sudo journalctl -u google-tasks-interceptor -n 50`

2. Verify environment:
   - `.env` file exists and contains `OPENAI_API_KEY`
   - Google credentials are valid in `secrets/credentials.json`
   - Virtual environment has all dependencies

3. Test manually:
   ```bash
   cd server
   export $(cat .env | xargs)
   python automated_workflow.py --test
   ```

### Authentication Issues

If you see Google authentication errors:

1. Delete the token file:
   ```bash
   rm server/secrets/token.json
   ```

2. Run manually to re-authenticate:
   ```bash
   python server/automated_workflow.py --test
   ```

3. Follow the browser prompt to authorize

### Permission Issues (Ubuntu)

Ensure proper permissions:
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/Things3-Android-Companion-App-Detailed
chmod 755 /home/ubuntu/Things3-Android-Companion-App-Detailed/server/automated_workflow.py
```

## Process Identification

The service runs with the process name `google-tasks-interceptor`, making it easy to identify:

- macOS: `ps aux | grep google-tasks-interceptor`
- Ubuntu: `systemctl status google-tasks-interceptor`

## Security Considerations

- The service runs with minimal privileges
- On Ubuntu, it uses systemd security features like `ProtectSystem` and `PrivateTmp`
- Credentials are stored locally and never transmitted except to authorized APIs
- All processing happens locally except for OpenAI translation

## Monitoring Best Practices

1. Set up log rotation to prevent disk space issues
2. Monitor service health with monitoring tools
3. Set up alerts for service failures
4. Regularly check processed tasks CSV for accuracy 
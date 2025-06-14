# Things3 Today View to Google Tasks Sync

A lightweight utility to sync your Things3 Today view with Google Tasks.

## Features

- Automatic extraction of Today's tasks from Things3
- Sync with Google Tasks every 10 minutes
- Local backup of tasks in CSV format
- Detailed logging for monitoring
- macOS launch agent for continuous operation
- Minimal resource usage

## Prerequisites

- **macOS** with Things3 installed
- **Python 3.x** (included with macOS)
- Google account for Google Tasks integration

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/Things3-Android-Companion-App-Detailed.git
   cd Things3-Android-Companion-App-Detailed
   ```

2. Set up Python dependencies:

   ```bash
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 pandas
   ```

3. Set up Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Tasks API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download the credentials and save as `credentials.json` in the project directory

4. Copy the example configuration and update it:

   ```bash
   cp config.sh.example config.sh
   nano config.sh  # Review and update settings if needed
   ```

5. Make the sync script executable:

   ```bash
   chmod +x sync_today.sh
   ```

6. Run the initial sync manually to authorize Google Tasks:

   ```bash
   ./sync_today.sh
   ```
   
   This will open a browser window for Google OAuth authorization. After authorizing, a `token.json` file will be created.

## Automatic Startup (Launch Agent)

To run the sync automatically in the background every 10 minutes:

```bash
# Copy the launch agent to your user's LaunchAgents directory
cp com.things3.today_sync.plist ~/Library/LaunchAgents/

# Load and start the launch agent
launchctl load ~/Library/LaunchAgents/com.things3.today_sync.plist
launchctl start com.things3.today_sync
```

The agent will automatically start the sync script when you log in and run it every 10 minutes.

To stop the automatic sync:
```bash
launchctl unload ~/Library/LaunchAgents/com.things3.today_sync.plist
```

To check if the agent is running:
```bash
launchctl list | grep things3
```

## Configuration

The following configuration options are available in `config.sh`:

- `BACKUP_DIR`: Directory to store local backups (default: `~/ThingsBackups`)
- `THINGS_DB`: Path to your Things3 database (default: macOS default location)
- `LOCAL_CSV`: Local CSV file to store tasks (default: `today_view.csv`)
- `EXTRACT_SCRIPT`: Script to extract tasks (default: `extract_tasks.py`)
- `GOOGLE_TASKS_SYNC`: Set to `1` to enable Google Tasks sync (default: `1`)
- `LOG_FILE`: Path to log file (default: `sync.log`)

## Usage

### Manual Sync

Run a single sync operation:
```bash
./sync_today.sh
```

### Logs and Monitoring

- View the main sync log:
  ```bash
  tail -f sync.log
  ```
  
- View detailed logs:
  ```bash
  # Standard output
  tail -f /tmp/things3_sync_stdout.log
  
  # Error output
  tail -f /tmp/things3_sync_stderr.log
  ```

- View the latest Today view CSV:
  ```bash
  cat today_view.csv
  ```

- Check the service status:
  ```bash
  launchctl list | grep things3
  ```

## Google Tasks Integration

The sync script automatically handles Google Tasks integration when `GOOGLE_TASKS_SYNC` is enabled in `config.sh`.

### First-time Setup

1. Run the sync manually once to authorize Google Tasks:

   ```bash
   ./sync_today.sh
   ```

2. A browser window will open for Google OAuth authorization
3. After authorizing, a `token.json` file will be created

### How It Works
- Tasks are extracted from Things3 and saved to `today_view.csv`
- The script then syncs these tasks with your default Google Tasks list
- Only tasks that don't already exist in Google Tasks will be added
- The sync runs automatically every 10 minutes

## Troubleshooting

### Common Issues

1. **Google Authentication Errors**

   - Delete the `token.json` file and run `./sync_today.sh` to re-authenticate
   - Ensure your `credentials.json` is correctly set up in the Google Cloud Console

2. **Sync Not Starting**

   - Check if the launch agent is loaded: `launchctl list | grep things3`
   - Check the log files:

     ```bash
     tail -f sync.log
     tail -f /tmp/things3_sync_*.log
     ```

   - Try running the sync manually: `./sync_today.sh`

3. **Things3 Database Not Found**

   - Verify the path to your Things3 database in `config.sh`
   - The default path is for the standard macOS installation

4. **Python Dependencies**
   - Ensure all required packages are installed:
     ```bash
    pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 pandas
     ```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Things3 ↔ Google Tasks Local Sync

**A local macOS solution for syncing your tasks.** This project provides two-way 
synchronization between Things3 and Google Tasks, enabling access to your to-dos 
on any device while running entirely on your Mac.

## Features

- **Two-way synchronization** – Changes in Google Tasks sync back to Things3
- **Completed task sync** – Tasks completed in Google Tasks are marked complete in Things3
- **Multi-list support** – Sync Today, Upcoming, Anytime, and Someday lists
- **English task processing** – Automatically translate English tasks to Hebrew (optional)
- **Local automation** – Runs entirely on your Mac with LaunchAgent scheduling
- **Smart duplicate handling** – Prevents duplicate tasks across lists

## Prerequisites

- **macOS** with Things3 installed
- **Python 3.x** with pip
- Google account for Google Tasks
- Things3 auth token (see setup)

## Setup

1. Clone this repository and navigate to it:
   ```bash
   git clone https://github.com/yourusername/Things3-Android-Companion-App.git
   cd Things3-Android-Companion-App
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

3. Get your Things3 auth token:
   - Open Things3 on Mac
   - Go to **Things** → **Settings** → **General**
   - Click **Enable Things URLs** → **Manage**
   - Copy your auth token

4. Set the auth token in your environment:
   ```bash
   export THINGS_AUTH_TOKEN="your-token-here"
   echo 'export THINGS_AUTH_TOKEN="your-token-here"' >> ~/.zshrc
   ```

5. (Optional) For English to Hebrew translation, set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   echo 'export OPENAI_API_KEY="your-key-here"' >> ~/.zshrc
   ```

## Installation

Install the automated sync to run every 30 minutes:

```bash
./install_local_sync.sh
```

The sync will now run automatically in the background. To check status:
```bash
launchctl list | grep com.things3.local_sync
```

## Manual Usage

Run the complete sync workflow manually:
```bash
./local_sync_workflow.sh
```

This will:
1. Extract tasks from Things3 to CSV files
2. Sync tasks to Google Tasks
3. Sync changes from Google Tasks back to Things3
4. Process English tasks (if OpenAI key is set)

## How It Works

### Workflow Steps

1. **Extract** - AppleScript extracts tasks from Things3 into CSV files
2. **Upload** - Tasks are synced to Google Tasks, maintaining mappings
3. **Monitor** - Changes in Google Tasks are detected
4. **Update** - Things3 is updated via URL scheme for:
   - Due date changes
   - Task completions (marks complete in Things3, then deletes from Google)
   - Deleted tasks

### File Structure

```
outputs/
├── today_view.csv         # Extracted Today tasks
├── upcoming_tasks.csv     # Extracted Upcoming tasks
├── anytime_tasks.csv      # Extracted Anytime tasks
├── someday_tasks.csv      # Extracted Someday tasks
├── task_mapping.json      # Maps Things3 UUIDs to Google Task IDs
├── sync_state.json        # Tracks task states for change detection
└── local_sync_workflow.log # Sync operation logs
```

## Configuration

Edit `config.sh` to customize:
- `GOOGLE_TASKS_SYNC` - Set to 1 to sync all lists (not just Today)
- Log retention settings
- File paths

## Testing

Run the test suite to verify your setup:
```bash
python3 test_local_workflow.py
```

This tests:
- Things3 to Google Tasks sync
- All lists synchronization
- Completed task sync
- English task processing (if configured)

## Troubleshooting

### Common Issues

1. **"No Things3 UUID found"** - Normal for tasks created directly in Google Tasks
2. **Auth token errors** - Verify your Things3 auth token is correct
3. **Sync not running** - Check LaunchAgent status with `launchctl list`

### View Logs

```bash
# Main workflow log
tail -f outputs/local_sync_workflow.log

# Two-way sync details
tail -f outputs/two_way_sync.log
```

### Reset Sync

To start fresh:
```bash
rm outputs/task_mapping.json outputs/sync_state.json
./local_sync_workflow.sh
```

## Uninstall

To remove the automated sync:
```bash
launchctl unload ~/Library/LaunchAgents/com.things3.local_sync.plist
rm ~/Library/LaunchAgents/com.things3.local_sync.plist
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

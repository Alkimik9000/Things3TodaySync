# Automated Things3 Workflow Guide

## Overview

The automated workflow system continuously monitors your Google Tasks for English tasks, translates them to Hebrew with emojis using OpenAI, generates Things3 URLs, and tests them locally. The system runs every 30 seconds and maintains state to prevent duplicate processing.

## Features

✅ **Continuous Monitoring**: Checks Google Tasks every 30 seconds  
✅ **Smart Duplicate Prevention**: Tracks processed tasks to avoid reprocessing  
✅ **Hebrew Translation**: Uses OpenAI to translate tasks with GTD principles  
✅ **Emoji Enhancement**: Adds two relevant emojis to each translated task  
✅ **Local URL Testing**: Tests Things3 URLs on macOS using the `open` command  
✅ **Comprehensive Logging**: Logs all actions to file and console  
✅ **CSV Export**: Saves original and translated tasks to CSV files  
✅ **State Management**: Maintains processing state across restarts  

## Prerequisites

1. **Environment Setup**:
   ```bash
   # Create .env file in server directory
   OPENAI_API_KEY="your-openai-api-key-here"
   ```

2. **Google Credentials**:
   - Place `credentials.json` in `server/secrets/`
   - The system will handle token generation on first run

3. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Option 1: Single Test Run
```bash
cd server
python automated_workflow.py --test
```
This runs one monitoring cycle to test the system.

### Option 2: Continuous Monitoring
```bash
cd server
python automated_workflow.py
```
This runs continuous monitoring every 30 seconds. Press Ctrl+C to stop.

### Option 3: Using the Shell Script
```bash
cd server
./run_every_30s.sh
```
This also starts continuous monitoring with additional Flask server setup.

## How It Works

1. **Monitor**: Checks Google Tasks default list for new English tasks
2. **Filter**: Identifies tasks with English letters that haven't been processed
3. **Translate**: Uses OpenAI to translate to Hebrew with GTD principles + emojis
4. **Generate URL**: Creates Things3 URL with title, notes, due date, scheduled for "today"
5. **Test Locally**: Opens the URL on macOS to verify it works
6. **Clean Up**: Deletes the original English task from Google Tasks
7. **Save**: Records processed task in CSV and state files
8. **Repeat**: Waits 30 seconds and repeats

## Generated Files

- `outputs/processed_tasks.csv` - All processed tasks with translations
- `processed_task_ids.json` - State file tracking processed task IDs
- `automated_workflow.log` - Comprehensive log of all operations
- `apple_shortcuts/generated_things_urls.txt` - Generated Things3 URLs

## Example Workflow

1. Add English task to Google Tasks: "Buy groceries for the weekend"
2. System detects it and translates to: "קניית מצרכים לסופ"ש 🛒🍎"
3. Generates Things3 URL: `things:///add?title=...&when=today&deadline=...`
4. Tests URL locally (opens Things3 on macOS)
5. Deletes original task from Google Tasks
6. Saves to CSV with both original and translated versions

## Monitoring and Logs

The system provides detailed logging:

```
2025-06-18 17:33:41,787 - INFO - 🔄 Starting monitoring cycle...
2025-06-18 17:33:42,405 - INFO - Found 1 new English tasks
2025-06-18 17:33:42,405 - INFO - Processing task: Buy groceries for the weekend
2025-06-18 17:33:43,966 - INFO - Translated 'Buy groceries for the weekend' to 'קניית מצרכים לסופ"ש 🛒🍎'
2025-06-18 17:33:44,087 - INFO - ✅ URL opened successfully for: קניית מצרכים לסופ"ש 🛒🍎
2025-06-18 17:33:44,820 - INFO - ✅ Deleted task from Google Tasks: Buy groceries for the weekend
2025-06-18 17:33:44,832 - INFO - ✅ Successfully processed 1 tasks
```

## Production Deployment

For server deployment:

1. **Systemd Service** (Linux):
   ```bash
   sudo systemctl enable things3-automation
   sudo systemctl start things3-automation
   ```

2. **LaunchAgent** (macOS):
   Create `~/Library/LaunchAgents/com.things3.automation.plist`

3. **Docker Container**:
   Run the automation in a containerized environment

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check your API key and quota
2. **Google Auth Errors**: Delete `secrets/token.json` to re-authenticate
3. **Things3 URL Errors**: Ensure Things3 is installed on macOS
4. **Permission Errors**: Check file permissions in outputs directory

### Debug Mode

Run with verbose logging:
```bash
python automated_workflow.py --test
```

Check log files:
```bash
tail -f automated_workflow.log
```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Google credentials are stored locally in `secrets/token.json`
- All processing happens locally; only OpenAI translation requires external API

## Integration with Apple Shortcuts

The generated URLs can be served via the Flask server for iOS Shortcuts integration:

```bash
cd apple_shortcuts
python serve_urls.py
```

Then access URLs via: `http://localhost:5000/task/1` 
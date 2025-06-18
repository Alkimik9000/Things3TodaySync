# iOS/iPadOS Apple Shortcut Setup Guide

## Overview
This guide walks you through creating an Apple Shortcut that automatically fetches Things3 URLs from your server and creates tasks in Things3.

## Prerequisites
- iOS/iPadOS device with Shortcuts app
- Things3 app installed
- Server running with Flask URL server
- Server IP address and API key

## Step-by-Step Setup

### 1. Create New Shortcut
1. Open the Shortcuts app
2. Tap the "+" to create a new shortcut
3. Name it "Sync Things3 Tasks"

### 2. Add Actions

#### Step 1: Set Variables
Add these actions in order:

1. **Text** action
   - Enter your server URL: `http://<your-server-ip>:5000/new_urls`
   - Name this variable "ServerURL"

2. **Text** action
   - Enter your API key: `your-api-key-here`
   - Name this variable "APIKey"

#### Step 2: Make API Request
1. **Get Contents of URL** action
   - URL: Select "ServerURL" variable
   - Method: GET
   - Headers: Add new header
     - Key: `Authorization`
     - Value: Text with `Bearer ` followed by "APIKey" variable

#### Step 3: Parse Response
1. **Get Dictionary Value** action
   - Dictionary: Contents of URL
   - Get: Value for "urls"
   - Name result "URLsList"

#### Step 4: Process Each URL
1. **Repeat with Each** action
   - Repeat with each item in "URLsList"

2. Inside the repeat block, add:
   - **Get Dictionary Value** action
     - Dictionary: Repeat Item
     - Get: Value for "url"
     - Name result "TaskURL"
   
   - **Open URLs** action
     - Open: "TaskURL" variable

#### Step 5: Optional - Add Delay
1. **Wait** action (optional)
   - Wait: 1 second
   - This prevents overwhelming Things3 with rapid URL opens

### 3. Configure Automation

#### Option A: Manual Run
- Add shortcut to Home Screen or Widget
- Run manually when needed

#### Option B: Automatic Schedule
1. Go to Shortcuts → Automation tab
2. Create Personal Automation
3. Choose "Time of Day"
4. Set to run every 30 minutes (or your preference)
5. Select your "Sync Things3 Tasks" shortcut
6. Turn off "Ask Before Running"

#### Option C: Location-Based
1. Create automation triggered by:
   - Arriving at work/home
   - Connecting to specific WiFi
   - Opening Things3 app

### 4. Error Handling (Advanced)

Add these optional improvements:

1. **If** action after "Get Contents of URL"
   - If: Contents of URL has any value
   - Otherwise: Show notification "Failed to connect to server"

2. **Count** action after getting URLs
   - Count: Items in "URLsList"
   - Show notification with count of new tasks

### 5. Complete Shortcut Structure

```
1. Text (ServerURL) → http://192.168.1.100:5000/new_urls
2. Text (APIKey) → your-api-key
3. Get Contents of URL
   - URL: ServerURL
   - Headers: Authorization: Bearer [APIKey]
4. Get Dictionary Value → urls → URLsList
5. Count (URLsList) → TaskCount
6. If (TaskCount > 0)
   - Repeat with Each (URLsList)
     - Get Dictionary Value → url → TaskURL
     - Open URLs (TaskURL)
     - Wait 1 second
   - Show Notification "Added [TaskCount] tasks"
7. Otherwise
   - Show Notification "No new tasks"
```

## Testing

1. **Test Server Connection**:
   - Run shortcut manually
   - Check if tasks appear in Things3
   - Verify server marks tasks as processed

2. **Test Automation**:
   - Create test task in server
   - Wait for automation to run
   - Confirm task appears in Things3

## Troubleshooting

### "Cannot connect to server"
- Check server is running: `curl http://<server-ip>:5000/status`
- Verify device is on same network
- Check firewall settings

### "Unauthorized" error
- Verify API key matches server setting
- Check Authorization header format: `Bearer <key>`

### Tasks not appearing in Things3
- Ensure Things3 is installed
- Check URL format in server logs
- Try opening a URL manually in Safari

### Shortcut runs but nothing happens
- Add notification actions for debugging
- Check server logs for requests
- Verify CSV has unprocessed tasks

## Security Notes

1. **API Key Storage**:
   - Don't share shortcuts containing API keys
   - Consider using Shortcuts input for key

2. **Network Security**:
   - Use VPN for remote access
   - Consider HTTPS for production
   - Restrict server to local network

## Advanced Features

### Batch Processing
Instead of opening each URL individually:
1. Combine all URLs with line breaks
2. Copy to clipboard
3. Use Things3 URL scheme to import multiple tasks

### Selective Sync
Add filters to process only certain tasks:
1. Filter by project
2. Filter by tags
3. Filter by date range

### Two-Way Sync
Future enhancement to update task status:
1. Get completed tasks from Things3
2. Send status back to server
3. Update processed_tasks.csv

## Example Server Response

```json
{
  "urls": [
    {
      "task_number": "0001",
      "title": "Buy groceries",
      "url": "things:///add?title=Buy%20groceries&when=today"
    },
    {
      "task_number": "0002", 
      "title": "Call dentist",
      "url": "things:///add?title=Call%20dentist&when=today&deadline=2024-06-20"
    }
  ],
  "count": 2
}
```

## Support

For issues or questions:
1. Check server logs: `tail -f flask_server.log`
2. Test API manually: `curl -H "Authorization: Bearer <key>" http://<server>:5000/new_urls`
3. Review Things3 URL scheme documentation 
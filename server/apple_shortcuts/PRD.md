# Product Requirements Document (PRD) - Apple Shortcuts Integration

## Purpose
Automate the creation and execution of Things3 tasks on iOS/iPadOS devices using generated URLs from processed tasks. This system bridges the gap between server-side task processing and mobile task management.

## Overview
The Apple Shortcuts integration consists of server-side components that generate Things3 URLs and serve them via a web API, paired with iOS/iPadOS shortcuts that fetch and execute these URLs automatically.

## Features

### 1. URL Generation and Storage
- **GenUrl Column**: Automatically added to `processed_tasks.csv` containing Things3 URLs
- **URL Format**: `things:///add?title=...&when=today[&deadline=...][&notes=...]`
- **Automatic Generation**: URLs created for all new tasks with TaskNumber > last processed

### 2. URL Serving via Web API
- **Flask Server**: Lightweight web server (`serve_urls.py`) running on port 5000
- **Endpoints**:
  - `GET /new_urls` - Returns unprocessed URLs (requires authentication)
  - `GET /status` - Server status and statistics
  - `GET /` - Simple index page
- **Authentication**: Bearer token via Authorization header
- **Auto-update**: Marks URLs as processed after serving

### 3. Processing Status Tracking
- **Processed Column**: Tracks URL delivery status ("Yes"/"No")
- **State Management**: Prevents duplicate processing
- **Batch Processing**: Serves multiple URLs in single request

## Requirements

### Server-Side Requirements
1. **URL Generation** (`create_things_links.py`):
   - Detect new rows in `processed_tasks.csv` (TaskNumber > last_linked_task.txt)
   - Generate Things3 URLs with:
     - `title`: Task title (required)
     - `when=today`: Schedule for today (always included)
     - `deadline`: Due date if present (YYYY-MM-DD format)
     - `notes`: Task notes if present
   - Store URLs in "GenUrl" column
   - Initialize "Processed" as "No" for new URLs

2. **URL Server** (`serve_urls.py`):
   - Flask server on configurable port (default: 5000)
   - Return JSON response with unprocessed URLs
   - Update "Processed" to "Yes" after serving
   - Simple API key authentication

3. **Automation** (`run_every_30s.sh`):
   - Run `process_english_tasks.py` every 30 seconds
   - Run `create_things_links.py` to generate URLs
   - Start Flask server if not running
   - Log all operations

### iOS/iPadOS Requirements
1. **Apple Shortcut Configuration**:
   - Fetch URLs from server endpoint
   - Parse JSON response
   - Open each URL in Things3
   - Run periodically (every 30-60 seconds)

## API Specification

### GET /new_urls
**Request:**
```
GET http://<server-ip>:5000/new_urls
Authorization: Bearer <api-key>
```

**Response:**
```json
{
  "urls": [
    {
      "task_number": "0001",
      "title": "Task Title",
      "url": "things:///add?title=..."
    }
  ],
  "count": 1
}
```

### GET /status
**Response:**
```json
{
  "status": "ok",
  "statistics": {
    "total_tasks": 10,
    "tasks_with_urls": 8,
    "processed": 5,
    "unprocessed": 3
  }
}
```

## Security Considerations

1. **API Authentication**:
   - Use environment variable `THINGS_API_KEY` for API key
   - Bearer token authentication required for `/new_urls`
   - No authentication for status endpoint

2. **Network Security**:
   - Run on localhost for local-only access
   - Use private network IP for LAN access
   - Consider VPN for remote access
   - HTTPS recommended for production

3. **Data Protection**:
   - No sensitive data in URLs
   - Task content URL-encoded
   - No persistent storage of served URLs

## Configuration

### Environment Variables
- `THINGS_API_KEY`: API key for authentication (default: "default-api-key")
- `FLASK_PORT`: Server port (default: 5000)
- `FLASK_HOST`: Server host (default: "0.0.0.0")

### Files
- `processed_tasks.csv`: Source data with GenUrl and Processed columns
- `last_linked_task.txt`: Tracks last processed TaskNumber
- `generated_things_urls.txt`: Legacy URL storage
- `flask_server.log`: Server logs

## Workflow

1. **Task Processing**:
   - New task added to `processed_tasks.csv`
   - `create_things_links.py` generates URL
   - URL stored in GenUrl column, Processed = "No"

2. **URL Serving**:
   - iOS device requests `/new_urls`
   - Server returns unprocessed URLs
   - Server updates Processed = "Yes"

3. **Task Creation**:
   - iOS Shortcut opens each URL
   - Things3 creates task with properties
   - Task appears in Today view

## Error Handling

- **Missing CSV**: Returns 404 error
- **Missing Columns**: Returns 500 error with details
- **Invalid Authentication**: Returns 401 error
- **Server Errors**: Logged to flask_server.log

## Future Enhancements

1. **Webhook Support**: Push notifications for new URLs
2. **Batch Processing**: Process multiple URLs in Things3
3. **Two-way Sync**: Update task status back to server
4. **Multiple Lists**: Support for different Things3 lists
5. **Priority Levels**: Add task priority support
6. **Rich Formatting**: Support for markdown in notes 
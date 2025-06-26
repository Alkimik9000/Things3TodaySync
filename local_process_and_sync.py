#!/usr/bin/env python3
"""Local process and sync for Google Tasks to Things3 workflow.

This script:
1. Fetches English tasks from Google Tasks
2. Translates them to Hebrew using OpenAI
3. Adds them to Things3 Today view via URL scheme
4. Maintains tracking of processed tasks to avoid duplicates
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import openai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
SCOPES = ["https://www.googleapis.com/auth/tasks"]
OUTPUT_DIR = Path("outputs")
TOKEN_FILE = Path("secrets/token.json")
CREDENTIALS_FILE = Path("secrets/credentials.json")
PROCESSED_TASKS_FILE = OUTPUT_DIR / "processed_tasks.json"
TASK_MAPPING_FILE = OUTPUT_DIR / "task_mapping.json"
LOG_FILE = OUTPUT_DIR / "local_sync.log"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def getGoogleTasksService() -> Any:
    """Authorize and return a Google Tasks service instance."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return build("tasks", "v1", credentials=creds)


def isEnglish(text: str) -> bool:
    """Return True if text contains any English letters."""
    return bool(re.search(r"[A-Za-z]", text))


def translateToHebrew(text: str, add_emojis: bool = True) -> str:
    """Use OpenAI API to translate text to Hebrew."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    openai.api_key = api_key
    
    if add_emojis:
        system_content = (
            "You translate task titles from English to Hebrew and rewrite "
            "them concisely following Getting Things Done principles. "
            "Add two relevant emojis at the end of the sentence."
        )
    else:
        system_content = (
            "You are a Hebrew translator. Translate the given English text to Hebrew. "
            "Do NOT add any emojis. Just provide a pure Hebrew translation."
        )
    
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": text},
    ]
    response: Any = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return str(response["choices"][0]["message"]["content"]).strip()


def loadProcessedTasks() -> Set[str]:
    """Load set of already processed task IDs."""
    if PROCESSED_TASKS_FILE.exists():
        with open(PROCESSED_TASKS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get("processed_ids", []))
    return set()


def saveProcessedTasks(processed_ids: Set[str]) -> None:
    """Save set of processed task IDs."""
    with open(PROCESSED_TASKS_FILE, 'w') as f:
        json.dump({
            "processed_ids": list(processed_ids),
            "last_update": datetime.now().isoformat()
        }, f, indent=2)


def addToThings3(title: str, notes: str = "", due_date: Optional[str] = None) -> bool:
    """Add a task to Things3 using URL scheme."""
    # Build the URL
    params = {
        'title': title,
        'when': 'today',  # Always add to Today
        'reveal': 'false'  # Don't switch to Things3
    }
    
    if notes:
        params['notes'] = notes
    
    if due_date:
        # Convert Google date format to Things3 format
        try:
            dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            params['deadline'] = dt.strftime('%Y-%m-%d')
        except:
            pass  # Skip if date parsing fails
    
    # Encode parameters
    query_string = urllib.parse.urlencode(params)
    url = "things:///add?" + query_string
    
    try:
        # Open the URL on macOS
        result = subprocess.run(
            ["open", url],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error adding to Things3: {e}")
        return False


def processEnglishTasks() -> None:
    """Main function to process English tasks from Google Tasks."""
    service = getGoogleTasksService()
    processed_ids = loadProcessedTasks()
    
    # Get all tasks from default list
    all_tasks = []
    page_token = None
    
    while True:
        if page_token:
            response = service.tasks().list(
                tasklist="@default",
                pageToken=page_token,
                maxResults=100,
                showCompleted=False,
                showHidden=False
            ).execute()
        else:
            response = service.tasks().list(
                tasklist="@default",
                maxResults=100,
                showCompleted=False,
                showHidden=False
            ).execute()
        
        all_tasks.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    
    # Process English tasks
    new_processed = 0
    for task in all_tasks:
        task_id = task.get("id")
        title = task.get("title", "")
        notes = task.get("notes", "")
        due = task.get("due")
        
        # Skip if already processed
        if task_id in processed_ids:
            continue
        
        # Skip if not English
        if not isEnglish(title):
            continue
        
        print(f"Processing: {title}")
        
        # Translate to Hebrew
        hebrew_title = translateToHebrew(title, add_emojis=True)
        hebrew_notes = ""
        if notes and isEnglish(notes):
            hebrew_notes = translateToHebrew(notes, add_emojis=False)
        
        # Add to Things3
        if addToThings3(hebrew_title, hebrew_notes, due):
            print(f"  ✓ Added to Things3: {hebrew_title}")
            
            # Mark as processed
            processed_ids.add(task_id)
            new_processed += 1
            
            # Delete from Google Tasks
            try:
                service.tasks().delete(tasklist="@default", task=task_id).execute()
                print(f"  ✓ Deleted from Google Tasks")
            except Exception as e:
                print(f"  ❌ Failed to delete from Google Tasks: {e}")
        else:
            print(f"  ❌ Failed to add to Things3")
    
    # Save processed IDs
    saveProcessedTasks(processed_ids)
    
    # Log summary
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - Processed {new_processed} new English tasks\n")
    
    print(f"\nSummary: Processed {new_processed} new English tasks")


if __name__ == "__main__":
    processEnglishTasks() 
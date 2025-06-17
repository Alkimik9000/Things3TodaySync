#!/usr/bin/env python3
"""One-time cleanup script to remove all Google Tasks lists and tasks."""

from __future__ import annotations
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_FILE = os.path.join("secrets", "token.json")
CREDENTIALS_FILE = os.path.join("secrets", "credentials.json")


def getService():
    """Authorize the user and return a Google Tasks service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or request new credentials if necessary
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("tasks", "v1", credentials=creds)


def cleanupAllTasks():
    """Remove all tasks from all task lists and delete non-default lists."""
    service = getService()
    
    print("Starting Google Tasks cleanup...")
    
    # Get all task lists
    tasklists = service.tasklists().list().execute()
    
    for tasklist in tasklists.get('items', []):
        list_id = tasklist['id']
        list_title = tasklist['title']
        
        print(f"\nProcessing list: {list_title} (ID: {list_id})")
        
        # Get all tasks in this list
        tasks = service.tasks().list(tasklist=list_id, showCompleted=True, showHidden=True).execute()
        task_items = tasks.get('items', [])
        
        # Delete all tasks
        for task in task_items:
            try:
                service.tasks().delete(tasklist=list_id, task=task['id']).execute()
                print(f"  Deleted task: {task.get('title', 'Untitled')}")
            except Exception as e:
                print(f"  Error deleting task: {e}")
        
        # Delete the list if it's not the default list
        if list_id != '@default':
            try:
                service.tasklists().delete(tasklist=list_id).execute()
                print(f"Deleted list: {list_title}")
            except Exception as e:
                print(f"Error deleting list {list_title}: {e}")
        else:
            # Update default list title to "Today"
            try:
                service.tasklists().update(
                    tasklist='@default',
                    body={'title': 'Today'}
                ).execute()
                print("Updated default list title to 'Today'")
            except Exception as e:
                print(f"Error updating default list title: {e}")
    
    print("\nCleanup completed!")


if __name__ == "__main__":
    cleanupAllTasks() 
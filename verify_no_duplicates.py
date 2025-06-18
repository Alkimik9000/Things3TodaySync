#!/usr/bin/env python3
"""Verify there are no duplicate tasks across Google Tasks lists."""

import os
from typing import Dict, List, Set
from collections import defaultdict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_FILE = os.path.join("secrets", "token.json")
CREDENTIALS_FILE = os.path.join("secrets", "credentials.json")


def canonTitle(title: str) -> str:
    """Return a canonical representation of a task title."""
    return " ".join(title.strip().split()).lower()


def getService():
    """Authorize the user and return a Google Tasks service instance."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("tasks", "v1", credentials=creds)


def checkForDuplicates():
    """Check for duplicate tasks across all Google Tasks lists."""
    service = getService()
    
    # Get all task lists
    tasklists = service.tasklists().list().execute()
    
    # Track tasks by canonical title
    tasks_by_title: Dict[str, List[Dict]] = defaultdict(list)
    all_tasks_count = 0
    
    print("Analyzing tasks across all lists...\n")
    
    for tasklist in tasklists.get('items', []):
        list_name = tasklist['title']
        list_id = tasklist['id']
        
        # Get all tasks in this list
        tasks_response = service.tasks().list(tasklist=list_id).execute()
        tasks = tasks_response.get('items', [])
        
        print("List: " + list_name + " (" + str(len(tasks)) + " tasks)")
        all_tasks_count += len(tasks)
        
        for task in tasks:
            title = task.get('title', '')
            canonical = canonTitle(title)
            
            task_info = {
                'title': title,
                'list': list_name,
                'id': task.get('id'),
                'notes': task.get('notes', ''),
                'due': task.get('due', '')
            }
            
            tasks_by_title[canonical].append(task_info)
    
    print("\nTotal tasks across all lists: " + str(all_tasks_count))
    
    # Check for duplicates within lists
    print("\n=== Checking for duplicates within lists ===")
    duplicates_within_lists = False
    
    for tasklist in tasklists.get('items', []):
        list_name = tasklist['title']
        list_id = tasklist['id']
        
        tasks_response = service.tasks().list(tasklist=list_id).execute()
        tasks = tasks_response.get('items', [])
        
        seen_in_list: Set[str] = set()
        for task in tasks:
            canonical = canonTitle(task.get('title', ''))
            if canonical in seen_in_list:
                print("DUPLICATE in " + list_name + ": " + task.get('title', ''))
                duplicates_within_lists = True
            seen_in_list.add(canonical)
    
    if not duplicates_within_lists:
        print("✅ No duplicates found within any list!")
    
    # Check for duplicates across lists
    print("\n=== Checking for duplicates across lists ===")
    duplicates_across_lists = False
    
    for canonical, task_list in tasks_by_title.items():
        if len(task_list) > 1:
            # Check if they're in different lists
            lists = {task['list'] for task in task_list}
            if len(lists) > 1:
                print("\nDUPLICATE across lists: '" + task_list[0]['title'] + "'")
                for task in task_list:
                    print("  - In " + task['list'])
                duplicates_across_lists = True
    
    if not duplicates_across_lists:
        print("✅ No duplicates found across lists!")
    
    # Summary
    print("\n=== Summary ===")
    unique_titles = len(tasks_by_title)
    print("Total unique task titles: " + str(unique_titles))
    
    if duplicates_within_lists or duplicates_across_lists:
        print("\n❌ Duplicates were found! Please run the sync again to clean them up.")
    else:
        print("\n✅ All good! No duplicates found in Google Tasks.")


if __name__ == "__main__":
    checkForDuplicates() 
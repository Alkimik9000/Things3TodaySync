#!/usr/bin/env python3
"""Test the local workflow including completed task sync."""

import subprocess
import time
import json
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
TOKEN_FILE = 'secrets/token.json'
MAPPING_FILE = 'outputs/task_mapping.json'
SCOPES = ['https://www.googleapis.com/auth/tasks']


def runCommand(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{description}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {description} successful")
        return True
    else:
        print(f"❌ {description} failed")
        print(f"Error: {result.stderr}")
        return False


def testThings3ToGoogleSync():
    """Test syncing from Things3 to Google Tasks."""
    print("\n=== Testing Things3 → Google Tasks Sync ===")
    
    # Extract tasks from Things3
    if not runCommand(['python3', 'extract_tasks.py'], "Extract Today tasks"):
        return False
    
    # Sync to Google Tasks
    if not runCommand(['python3', 'import_google_tasks.py'], "Import to Google Tasks"):
        return False
    
    return True


def testCompletedTaskSync():
    """Test the completed task sync workflow."""
    print("\n=== Testing Completed Task Sync ===")
    
    # Load task mapping
    if not Path(MAPPING_FILE).exists():
        print("❌ No task mapping file found. Run Things3 → Google sync first.")
        return False
    
    with open(MAPPING_FILE, 'r') as f:
        mappings = json.load(f)
    
    if not mappings:
        print("❌ No mapped tasks found")
        return False
    
    # Get Google Tasks service
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build('tasks', 'v1', credentials=creds)
    
    # Find a test task
    test_task = None
    for things_uuid, mapping in mappings.items():
        if mapping.get('google_id'):
            test_task = mapping
            test_task['things_uuid'] = things_uuid
            break
    
    if not test_task:
        print("❌ No suitable test task found")
        return False
    
    print(f"Using test task: {test_task['title']}")
    
    # Find which list the task is in
    tasklists = service.tasklists().list().execute()
    task_found = False
    tasklist_id = None
    
    for tasklist in tasklists.get('items', []):
        list_id = tasklist['id']
        try:
            task = service.tasks().get(tasklist=list_id, task=test_task['google_id']).execute()
            tasklist_id = list_id
            task_found = True
            print(f"  Found in list: {tasklist['title']}")
            break
        except:
            continue
    
    if not task_found:
        print("❌ Task not found in any Google Tasks list")
        return False
    
    # Mark as complete
    try:
        service.tasks().patch(
            tasklist=tasklist_id,
            task=test_task['google_id'],
            body={'status': 'completed'}
        ).execute()
        print("✓ Marked task as completed in Google Tasks")
    except Exception as e:
        print(f"❌ Failed to mark complete: {e}")
        return False
    
    # Run two-way sync
    time.sleep(2)
    if not runCommand(['python3', 'google_to_things_sync.py'], "Run two-way sync"):
        return False
    
    # Verify task was deleted from Google
    try:
        service.tasks().get(tasklist=tasklist_id, task=test_task['google_id']).execute()
        print("❌ Task still exists in Google Tasks (should have been deleted)")
        return False
    except:
        print("✓ Task deleted from Google Tasks after completion")
    
    return True


def testEnglishTaskProcessing():
    """Test English task processing."""
    print("\n=== Testing English Task Processing ===")
    
    # Check if OpenAI key is available
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Skipping English task processing test (no OpenAI key)")
        return True
    
    # Add a test English task to Google Tasks
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build('tasks', 'v1', credentials=creds)
    
    test_task = {
        'title': 'Test task for workflow verification',
        'notes': 'This is a test task that should be processed'
    }
    
    try:
        result = service.tasks().insert(tasklist='@default', body=test_task).execute()
        print(f"✓ Added test English task: {test_task['title']}")
        test_task_id = result['id']
    except Exception as e:
        print(f"❌ Failed to add test task: {e}")
        return False
    
    # Run English task processing
    if not runCommand(['python3', 'local_process_and_sync.py'], "Process English tasks"):
        return False
    
    # Verify task was processed (deleted from Google)
    try:
        service.tasks().get(tasklist='@default', task=test_task_id).execute()
        print("❌ Test task still exists (should have been processed)")
        return False
    except:
        print("✓ Test task processed and removed from Google Tasks")
    
    return True


def testAllListsSync():
    """Test syncing all lists."""
    print("\n=== Testing All Lists Sync ===")
    
    # Extract all lists
    lists = ['extract_tasks.py', 'extract_upcoming.py', 'extract_anytime.py', 'extract_someday.py']
    for script in lists:
        if not runCommand(['python3', script], f"Extract {script.replace('extract_', '').replace('.py', '')}"):
            return False
    
    # Sync all lists
    if not runCommand(['python3', 'import_google_tasks.py', '--all'], "Sync all lists to Google Tasks"):
        return False
    
    return True


def main():
    """Run all tests."""
    print("Testing Local Workflow")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 4
    
    # Test 1: Things3 to Google sync
    if testThings3ToGoogleSync():
        tests_passed += 1
    
    # Test 2: All lists sync
    if testAllListsSync():
        tests_passed += 1
    
    # Test 3: Completed task sync
    if testCompletedTaskSync():
        tests_passed += 1
    
    # Test 4: English task processing
    if testEnglishTaskProcessing():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
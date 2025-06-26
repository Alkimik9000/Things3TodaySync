#!/usr/bin/env python3
"""Two-way sync from Google Tasks to Things3.

This script monitors Google Tasks for changes and updates Things3 accordingly:
1. Due date changes are synced to Things3
2. Completed tasks in Google are marked complete in Things3, then deleted from Google
3. Deleted tasks in Google are removed from Things3
"""

from __future__ import annotations

import json
import os
import sys
import subprocess
import urllib.parse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_FILE = os.path.join("secrets", "token.json")
CREDENTIALS_FILE = os.path.join("secrets", "credentials.json")
MAPPING_FILE = os.path.join("outputs", "task_mapping.json")
SYNC_STATE_FILE = os.path.join("outputs", "sync_state.json")
LOG_FILE = os.path.join("outputs", "two_way_sync.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TwoWaySync:
    """Handles two-way synchronization between Google Tasks and Things3."""
    
    def __init__(self):
        self.service = self._getService()
        self.task_mapping = self._loadTaskMapping()
        self.sync_state = self._loadSyncState()
        self.things_auth_token = self._getThingsAuthToken()
        
    def _getService(self) -> Any:
        """Authorize and return a Google Tasks service instance."""
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
    
    def _loadTaskMapping(self) -> Dict[str, Dict[str, str]]:
        """Load the mapping between Things3 UUIDs and Google Task IDs."""
        if os.path.exists(MAPPING_FILE):
            with open(MAPPING_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _saveTaskMapping(self) -> None:
        """Save the task mapping to file."""
        os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)
        with open(MAPPING_FILE, 'w') as f:
            json.dump(self.task_mapping, f, indent=2)
    
    def _loadSyncState(self) -> Dict[str, Any]:
        """Load the sync state to track changes."""
        if os.path.exists(SYNC_STATE_FILE):
            with open(SYNC_STATE_FILE, 'r') as f:
                return json.load(f)
        return {"last_sync": None, "task_states": {}}
    
    def _saveSyncState(self) -> None:
        """Save the sync state."""
        os.makedirs(os.path.dirname(SYNC_STATE_FILE), exist_ok=True)
        with open(SYNC_STATE_FILE, 'w') as f:
            json.dump(self.sync_state, f, indent=2)
    
    def _getThingsAuthToken(self) -> str:
        """Get the Things3 auth token from environment or prompt user."""
        token = os.environ.get('THINGS_AUTH_TOKEN')
        if not token:
            logger.warning("THINGS_AUTH_TOKEN not found in environment variables.")
            logger.info("Please get your auth token from Things3:")
            logger.info("Mac: Things → Settings → General → Enable Things URLs → Manage")
            token = input("Enter your Things3 auth token: ").strip()
            if token:
                logger.info("Consider adding 'export THINGS_AUTH_TOKEN=\"{}\"' to your shell profile".format(token))
        return token
    
    def updateTaskMapping(self, things_uuid: str, google_task_id: str, task_title: str) -> None:
        """Update the mapping between Things3 and Google Tasks."""
        self.task_mapping[things_uuid] = {
            "google_id": google_task_id,
            "title": task_title,
            "last_synced": datetime.now().isoformat()
        }
        self._saveTaskMapping()
    
    def getGoogleTaskLists(self) -> Dict[str, str]:
        """Get all Google Task lists and their IDs."""
        tasklists = self.service.tasklists().list().execute()
        return {item['title']: item['id'] for item in tasklists.get('items', [])}
    
    def getGoogleTasks(self, list_id: str) -> List[Dict[str, Any]]:
        """Get all tasks from a Google Tasks list."""
        tasks = []
        page_token = None
        
        while True:
            if page_token:
                result = self.service.tasks().list(
                    tasklist=list_id,
                    pageToken=page_token,
                    maxResults=100,
                    showCompleted=True,
                    showHidden=True
                ).execute()
            else:
                result = self.service.tasks().list(
                    tasklist=list_id,
                    maxResults=100,
                    showCompleted=True,
                    showHidden=True
                ).execute()
            
            tasks.extend(result.get('items', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        
        return tasks
    
    def findThingsUUID(self, google_task_id: str) -> Optional[str]:
        """Find the Things3 UUID for a Google Task ID."""
        for things_uuid, mapping in self.task_mapping.items():
            if mapping.get('google_id') == google_task_id:
                return things_uuid
        return None
    
    def updateThingsTask(self, things_uuid: str, updates: Dict[str, Any]) -> bool:
        """Update a task in Things3 using URL scheme."""
        if not self.things_auth_token:
            logger.error("No Things3 auth token available")
            return False
        
        # Build the URL
        params = {
            'id': things_uuid,
            'auth-token': self.things_auth_token
        }
        params.update(updates)
        
        # Encode parameters
        query_string = urllib.parse.urlencode(params)
        url = "things:///update?" + query_string
        
        try:
            # Open the URL on macOS
            result = subprocess.run(
                ["open", url],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Successfully updated Things3 task: {}".format(things_uuid))
                return True
            else:
                logger.error("Failed to update Things3 task: {}".format(result.stderr))
                return False
                
        except Exception as e:
            logger.error("Error updating Things3 task: {}".format(e))
            return False
    
    def deleteGoogleTask(self, list_id: str, task_id: str) -> bool:
        """Delete a task from Google Tasks."""
        try:
            self.service.tasks().delete(tasklist=list_id, task=task_id).execute()
            logger.info("Deleted Google Task: {}".format(task_id))
            return True
        except Exception as e:
            logger.error("Failed to delete Google Task {}: {}".format(task_id, e))
            return False
    
    def convertGoogleDateToThings(self, google_date: str) -> str:
        """Convert Google Tasks date format to Things3 format."""
        # Google Tasks uses RFC 3339 format: 2024-12-25T00:00:00.000Z
        # Things3 expects: yyyy-mm-dd
        if not google_date:
            return ""
        
        try:
            # Parse the date - Google Tasks returns UTC dates
            # The issue was that we were parsing UTC time but not accounting for timezone
            from datetime import timezone
            
            # Parse as UTC
            dt = datetime.fromisoformat(google_date.replace('Z', '+00:00'))
            
            # For date-only tasks, Google Tasks sets time to 00:00:00 UTC
            # But this represents the date in the user's timezone, not UTC
            # So we need to return the date as-is, not convert timezone
            
            # Extract just the date part
            return dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error("Error parsing date {}: {}".format(google_date, e))
            return ""
    
    def deleteThingsTask(self, things_uuid: str) -> bool:
        """Delete a task in Things3 using URL scheme."""
        if not self.things_auth_token:
            logger.error("No Things3 auth token available")
            return False
        
        # Build the URL - Things3 doesn't have a direct delete URL, so we mark as cancelled
        params = {
            'id': things_uuid,
            'auth-token': self.things_auth_token,
            'canceled': 'true'
        }
        
        # Encode parameters
        query_string = urllib.parse.urlencode(params)
        url = "things:///update?" + query_string
        
        try:
            # Open the URL on macOS
            result = subprocess.run(
                ["open", url],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("Successfully deleted/cancelled Things3 task: {}".format(things_uuid))
                return True
            else:
                logger.error("Failed to delete Things3 task: {}".format(result.stderr))
                return False
                
        except Exception as e:
            logger.error("Error deleting Things3 task: {}".format(e))
            return False
    
    def detectChanges(self, google_task: Dict[str, Any], things_uuid: str) -> Dict[str, Any]:
        """Detect changes in a Google Task that need to be synced to Things3."""
        changes = {}
        task_id = google_task.get('id')
        
        # Get previous state
        prev_state = self.sync_state['task_states'].get(task_id, {})
        
        # Check completion status
        current_status = google_task.get('status', 'needsAction')
        prev_status = prev_state.get('status')
        
        # Always check if task is completed, regardless of previous state
        if current_status == 'completed':
            # If we don't have a previous state or it wasn't completed before
            if not prev_status or prev_status != 'completed':
                changes['completed'] = 'true'
                changes['mark_for_deletion'] = True
                logger.info("Task completed in Google: {}".format(google_task.get('title')))
        elif prev_status == 'completed' and current_status == 'needsAction':
            changes['completed'] = 'false'
            logger.info("Task marked incomplete in Google: {}".format(google_task.get('title')))
        
        # Check due date changes
        current_due = google_task.get('due')
        prev_due = prev_state.get('due')
        
        if current_due != prev_due:
            if current_due:
                things_date = self.convertGoogleDateToThings(current_due)
                if things_date:
                    changes['deadline'] = things_date
                    logger.info("Due date changed to {}: {}".format(things_date, google_task.get('title')))
            else:
                # Due date was removed
                changes['deadline'] = ''
                logger.info("Due date removed: {}".format(google_task.get('title')))
        
        # Update state for next comparison
        self.sync_state['task_states'][task_id] = {
            'status': current_status,
            'due': current_due,
            'title': google_task.get('title'),
            'updated': google_task.get('updated')
        }
        
        return changes
    
    def syncList(self, list_name: str, list_id: str) -> Tuple[int, int, int]:
        """Sync a specific Google Tasks list with Things3."""
        logger.info("Syncing list: {}".format(list_name))
        
        tasks = self.getGoogleTasks(list_id)
        synced_count = 0
        deleted_count = 0
        cancelled_count = 0
        
        for task in tasks:
            task_id = task.get('id')
            task_title = task.get('title', 'Untitled')
            
            if not task_id:
                logger.warning("Task has no ID: {}".format(task_title))
                continue
            
            # Find corresponding Things3 UUID
            things_uuid = self.findThingsUUID(task_id)
            
            if not things_uuid:
                # This task doesn't have a mapping yet - skip it
                logger.debug("No Things3 UUID found for Google Task: {}".format(task_title))
                continue
            
            # Detect changes
            changes = self.detectChanges(task, things_uuid)
            
            if changes:
                # Remove the deletion flag before updating Things3
                mark_for_deletion = changes.pop('mark_for_deletion', False)
                
                # Update Things3
                if self.updateThingsTask(things_uuid, changes):
                    synced_count += 1
                    
                    # If task was completed, delete from Google Tasks
                    if mark_for_deletion and task_id:
                        if self.deleteGoogleTask(list_id, task_id):
                            deleted_count += 1
                            # Remove from mapping
                            del self.task_mapping[things_uuid]
                            if task_id in self.sync_state['task_states']:
                                del self.sync_state['task_states'][task_id]
        
        return synced_count, deleted_count, cancelled_count
    
    def syncAll(self) -> None:
        """Sync all configured Google Tasks lists with Things3."""
        logger.info("Starting two-way sync from Google Tasks to Things3")
        
        # Get all task lists
        lists = self.getGoogleTaskLists()
        
        # Lists to sync
        sync_lists = ['Today', 'Upcoming', 'Anytime', 'Someday']
        
        total_synced = 0
        total_deleted = 0
        total_cancelled = 0
        
        # First, collect ALL Google task IDs from ALL lists
        all_google_task_ids: Set[str] = set()
        for list_name in sync_lists:
            if list_name in lists:
                tasks = self.getGoogleTasks(lists[list_name])
                for task in tasks:
                    task_id = task.get('id')
                    if task_id:
                        all_google_task_ids.add(task_id)
        
        # Now sync each list
        for list_name in sync_lists:
            if list_name in lists:
                synced, deleted, cancelled = self.syncList(list_name, lists[list_name])
                total_synced += synced
                total_deleted += deleted
                total_cancelled += cancelled
            else:
                logger.warning("List '{}' not found in Google Tasks".format(list_name))
        
        # After syncing all lists, check for tasks that were deleted from Google
        # (exist in mapping but not in any Google list)
        tasks_to_remove = []
        for things_uuid, mapping in self.task_mapping.items():
            google_id = mapping.get('google_id')
            # Only consider tasks that have a Google ID (were previously synced)
            # AND that Google ID no longer exists in any Google list
            if google_id and google_id not in all_google_task_ids:
                # Additional check: make sure this isn't a recently created task
                # by checking if it has a last_synced timestamp
                last_synced = mapping.get('last_synced')
                if last_synced:
                    # This task was previously synced but now deleted from Google
                    logger.info("Task deleted from Google, removing from Things3: {}".format(mapping.get('title')))
                    if self.deleteThingsTask(things_uuid):
                        total_cancelled += 1
                        tasks_to_remove.append(things_uuid)
                        # Remove from sync state
                        if google_id in self.sync_state['task_states']:
                            del self.sync_state['task_states'][google_id]
                else:
                    # This is a new task that hasn't been synced yet
                    logger.debug("Skipping deletion of unsynchronized task: {}".format(mapping.get('title')))
        
        # Remove deleted tasks from mapping
        for things_uuid in tasks_to_remove:
            del self.task_mapping[things_uuid]
        
        # Save state
        self.sync_state['last_sync'] = datetime.now().isoformat()
        self._saveSyncState()
        self._saveTaskMapping()
        
        logger.info("Sync completed. Updated: {}, Deleted from Google: {}, Cancelled in Things3: {}".format(
            total_synced, total_deleted, total_cancelled))

def main():
    """Main function."""
    try:
        sync = TwoWaySync()
        sync.syncAll()
    except KeyboardInterrupt:
        logger.info("Sync interrupted by user")
    except Exception as e:
        logger.error("Sync failed: {}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    main() 
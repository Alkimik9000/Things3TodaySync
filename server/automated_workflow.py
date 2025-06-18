#!/usr/bin/env python3
"""
Automated Things3 Workflow Monitor

This script continuously monitors Google Tasks for English tasks, translates them to Hebrew,
generates Things3 URLs, and tests them locally. It runs every 30 seconds and includes
comprehensive logging and error handling.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
OUTPUT_DIR = BASE_DIR / "outputs"
SECRETS_DIR = BASE_DIR / "secrets"
APPLE_SHORTCUTS_DIR = BASE_DIR / "apple_shortcuts"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = BASE_DIR / "automated_workflow.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SCOPES = ["https://www.googleapis.com/auth/tasks"]
TASKLIST_ID = os.getenv("GOOGLE_TASKS_LIST_ID", "@default")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_HOST = os.getenv("FLASK_HOST", "localhost")
CHECK_INTERVAL = 30  # seconds

class WorkflowAutomator:
    def __init__(self):
        self.processed_task_ids: Set[str] = set()
        self.flask_server_pid: Optional[int] = None
        self.last_check_time = datetime.now()
        
        # Load processed task IDs from state file
        self.state_file = BASE_DIR / "processed_task_ids.json"
        self.loadProcessedTaskIds()
        
    def loadProcessedTaskIds(self) -> None:
        """Load previously processed task IDs from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.processed_task_ids = set(data.get('processed_ids', []))
                logger.info("Loaded %d previously processed task IDs", len(self.processed_task_ids))
            except Exception as e:
                logger.error("Failed to load state file: %s", e)
                self.processed_task_ids = set()
    
    def saveProcessedTaskIds(self) -> None:
        """Save processed task IDs to state file."""
        try:
            data = {
                'processed_ids': list(self.processed_task_ids),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save state file: %s", e)
    
    def getGoogleTasksService(self) -> Any:
        """Get authenticated Google Tasks service."""
        creds = None
        token_file = SECRETS_DIR / "token.json"
        credentials_file = SECRETS_DIR / "credentials.json"
        
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('tasks', 'v1', credentials=creds)
    
    def isEnglishTask(self, title: str) -> bool:
        """Check if task title contains English letters."""
        import re
        return bool(re.search(r'[A-Za-z]', title))
    
    def translateToHebrew(self, title: str) -> str:
        """Translate English task to Hebrew with emojis using OpenAI."""
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        
        openai.api_key = api_key
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You translate task titles from English to Hebrew and rewrite "
                    "them concisely following Getting Things Done principles. "
                    "Add two relevant emojis at the end of the sentence."
                ),
            },
            {"role": "user", "content": title},
        ]
        
        try:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
            content = response.choices[0].message.content
            return str(content).strip() if content else title + " 📝✨"
        except Exception as e:
            logger.error("Translation failed for '%s': %s", title, e)
            return title + " 📝✨"  # Fallback with emojis
    
    def getNewEnglishTasks(self) -> List[Dict[str, Any]]:
        """Get new English tasks from Google Tasks that haven't been processed."""
        try:
            service = self.getGoogleTasksService()
            response = service.tasks().list(tasklist=TASKLIST_ID).execute()
            items = response.get("items", [])
            
            new_tasks = []
            for item in items:
                task_id = item.get("id", "")
                title = item.get("title", "")
                
                # Skip if already processed or not English
                if task_id in self.processed_task_ids:
                    continue
                
                if not self.isEnglishTask(title):
                    continue
                
                new_tasks.append(item)
            
            logger.info("Found %d new English tasks", len(new_tasks))
            return new_tasks
            
        except Exception as e:
            logger.error("Failed to fetch Google Tasks: %s", e)
            return []
    
    def processTask(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single task: translate and prepare for Things3."""
        try:
            task_id = task.get("id", "")
            title = task.get("title", "")
            notes = task.get("notes", "")
            due = task.get("due", "")
            
            logger.info("Processing task: %s", title)
            
            # Translate to Hebrew
            hebrew_title = self.translateToHebrew(title)
            
            # Create processed task data
            processed_task = {
                "id": task_id,
                "original_title": title,
                "hebrew_title": hebrew_title,
                "notes": notes,
                "due_date": due,
                "processed_at": datetime.now().isoformat()
            }
            
            # Mark as processed
            self.processed_task_ids.add(task_id)
            
            logger.info("Translated '%s' to '%s'", title, hebrew_title)
            return processed_task
            
        except Exception as e:
            logger.error("Failed to process task '%s': %s", task.get("title", ""), e)
            return None
    
    def generateThingsUrl(self, processed_task: Dict[str, Any]) -> str:
        """Generate Things3 URL for processed task."""
        title = processed_task["hebrew_title"]
        notes = processed_task["notes"]
        due = processed_task["due_date"]
        
        params = {"title": title, "when": "today"}
        
        if notes:
            params["notes"] = notes
        
        if due:
            # Convert ISO format to YYYY-MM-DD
            if "T" in due:
                due = due.split("T")[0]
            params["deadline"] = due
        
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        return f"things:///add?{query}"
    
    def testUrlLocally(self, url: str, task_title: str) -> bool:
        """Test Things3 URL locally by attempting to open it."""
        try:
            logger.info("Testing URL for task: %s", task_title)
            logger.info("URL: %s", url)
            
            # On macOS, use 'open' command to test the URL
            if sys.platform == "darwin":
                result = subprocess.run(
                    ["open", url],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("✅ URL opened successfully for: %s", task_title)
                    return True
                else:
                    logger.warning("⚠️ URL open failed for: %s (return code: %d)", task_title, result.returncode)
                    return False
            else:
                logger.info("URL testing skipped (not macOS): %s", task_title)
                return True
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ URL open timed out for: %s", task_title)
            return False
        except Exception as e:
            logger.error("❌ URL test failed for '%s': %s", task_title, e)
            return False
    
    def deleteProcessedTask(self, task_id: str, title: str) -> bool:
        """Delete processed task from Google Tasks."""
        try:
            service = self.getGoogleTasksService()
            service.tasks().delete(tasklist=TASKLIST_ID, task=task_id).execute()
            logger.info("✅ Deleted task from Google Tasks: %s", title)
            return True
        except Exception as e:
            logger.error("❌ Failed to delete task '%s': %s", title, e)
            return False
    
    def saveProcessedTasksToCSV(self, processed_tasks: List[Dict[str, Any]]) -> None:
        """Save processed tasks to CSV files."""
        if not processed_tasks:
            return
        
        try:
            # Prepare data for CSV
            csv_data = []
            for i, task in enumerate(processed_tasks, 1):
                csv_data.append({
                    "TaskNumber": f"{i:04d}",
                    "TaskTitle": task["hebrew_title"],
                    "TaskNotes": task["notes"],
                    "DueDate": task["due_date"],
                    "OriginalTitle": task["original_title"],
                    "ProcessedAt": task["processed_at"]
                })
            
            # Save to processed tasks CSV
            processed_csv = OUTPUT_DIR / "processed_tasks.csv"
            df = pd.DataFrame(csv_data)
            
            # Append to existing CSV or create new one
            if processed_csv.exists():
                existing_df = pd.read_csv(processed_csv)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_csv(processed_csv, index=False)
            logger.info("✅ Saved %d tasks to %s", len(csv_data), processed_csv)
            
        except Exception as e:
            logger.error("❌ Failed to save tasks to CSV: %s", e)
    
    def runSingleCycle(self) -> None:
        """Run a single monitoring cycle."""
        logger.info("🔄 Starting monitoring cycle...")
        
        # Get new English tasks
        new_tasks = self.getNewEnglishTasks()
        
        if not new_tasks:
            logger.info("No new English tasks found")
            return
        
        processed_tasks = []
        successful_urls = []
        
        # Process each task
        for task in new_tasks:
            processed_task = self.processTask(task)
            if not processed_task:
                continue
            
            # Generate Things3 URL
            things_url = self.generateThingsUrl(processed_task)
            processed_task["things_url"] = things_url
            
            # Test URL locally
            url_works = self.testUrlLocally(things_url, processed_task["hebrew_title"])
            processed_task["url_tested"] = url_works
            
            if url_works:
                successful_urls.append(things_url)
                
                # Delete from Google Tasks after successful processing
                if self.deleteProcessedTask(task["id"], task["title"]):
                    processed_tasks.append(processed_task)
        
        # Save processed tasks
        if processed_tasks:
            self.saveProcessedTasksToCSV(processed_tasks)
            self.saveProcessedTaskIds()
            
            logger.info("✅ Successfully processed %d tasks", len(processed_tasks))
            logger.info("🔗 Generated %d working URLs", len(successful_urls))
        
        logger.info("🏁 Cycle completed\n")
    
    def runContinuousMonitoring(self) -> None:
        """Run continuous monitoring every 30 seconds."""
        logger.info("🚀 Starting automated Things3 workflow monitor")
        logger.info("📝 Monitoring Google Tasks every %d seconds", CHECK_INTERVAL)
        logger.info("🛑 Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            while True:
                self.runSingleCycle()
                
                logger.info("⏰ Waiting %d seconds before next check...", CHECK_INTERVAL)
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error("❌ Monitoring failed: %s", e)
            raise
        finally:
            self.saveProcessedTaskIds()
            logger.info("💾 State saved. Goodbye!")

def loadEnvironmentVariables() -> None:
    """Load environment variables from .env file."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value

def validateSetup() -> bool:
    """Validate that all required files and environment variables are present."""
    logger.info("🔍 Validating setup...")
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not found in environment")
        return False
    
    # Check Google credentials
    credentials_file = SECRETS_DIR / "credentials.json"
    if not credentials_file.exists():
        logger.error("❌ Google credentials not found at %s", credentials_file)
        return False
    
    logger.info("✅ Setup validation passed")
    return True

def main() -> None:
    """Main function."""
    # Load environment variables
    loadEnvironmentVariables()
    
    # Validate setup
    if not validateSetup():
        logger.error("❌ Setup validation failed. Please check your configuration.")
        sys.exit(1)
    
    # Create and run automator
    automator = WorkflowAutomator()
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("🧪 Running in test mode (single cycle)")
        automator.runSingleCycle()
    else:
        automator.runContinuousMonitoring()

if __name__ == "__main__":
    main() 
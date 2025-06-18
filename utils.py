#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared utilities for Things3 extraction scripts.
Contains common functions used across multiple extraction modules.
"""

import subprocess
import pandas as pd
import os
import sys
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


def runAppleScript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("AppleScript error: " + str(e.stderr), file=sys.stderr)
        sys.exit(1)


def canonTitle(title: str) -> str:
    """Return a canonical representation of title for comparison."""
    return " ".join(title.strip().split()).lower()


def loadExistingTitles(csv_file: str) -> set[str]:
    """Return a set of canonical titles from csv_file if it exists."""
    if not os.path.exists(csv_file):
        return set()
    df = pd.read_csv(csv_file)
    df = df.fillna('')  # Replace NaN with empty strings
    return {canonTitle(str(t)) for t in df.get("ItemName", [])}


def getTaskCount(list_name: str) -> int:
    """Get count of tasks in specified Things3 list."""
    script = 'tell application "Things3" to count to dos of list "' + list_name + '"'
    count_str = runAppleScript(script)
    return int(count_str)


def getTaskProperty(index: int, property_name: str, list_name: str) -> str:
    """Get a specific property of a task by index from specified list."""
    script = 'tell application "Things3" to ' + property_name + ' of item ' + str(index) + ' of to dos of list "' + list_name + '"'
    result = runAppleScript(script)
    # Handle missing values
    if result == "missing value":
        return ""
    return result


def getTaskUUID(index: int, list_name: str) -> str:
    """Get UUID of a task by index from specified list."""
    script = 'tell application "Things3" to id of item ' + str(index) + ' of to dos of list "' + list_name + '"'
    result = runAppleScript(script)
    if result == "missing value":
        return ""
    return result


def getTaskTags(index: int, list_name: str) -> str:
    """Get tags for a task by index from specified list."""
    script = '''
    tell application "Things3"
        set theTags to tags of item ''' + str(index) + ''' of to dos of list "''' + list_name + '''"
        set tagList to ""
        repeat with aTag in theTags
            set tagList to tagList & name of aTag & "; "
        end repeat
        return tagList
    end tell
    '''
    tags = runAppleScript(script).strip()
    # Remove trailing "; "
    if tags.endswith("; "):
        tags = tags[:-2]
    return tags


def getFormattedDate(index: int, property_name: str, list_name: str) -> str:
    """Return Things3 date property formatted as YYYY-MM-DD or empty string."""
    script = '''
    tell application "Things3"
        set theDate to ''' + property_name + ''' of item ''' + str(index) + ''' of to dos of list "''' + list_name + '''"
        if theDate is missing value then
            return ""
        else
            set y to year of theDate as integer
            set m to month of theDate as integer
            set d to day of theDate as integer
            return (y as string) & "," & (m as string) & "," & (d as string)
        end if
    end tell
    '''
    raw_result = runAppleScript(script)
    if not raw_result:
        return ""
    try:
        y_str, m_str, d_str = [part.strip() for part in raw_result.split(",")]
        y, m, d = int(y_str), int(m_str), int(d_str)
        return "%04d" % y + "-" + "%02d" % m + "-" + "%02d" % d
    except ValueError:
        return ""


def getFormattedTime(index: int, property_name: str, list_name: str) -> str:
    """Return Things3 time component as HH:MM or empty string."""
    script = '''
    tell application "Things3"
        set theDate to ''' + property_name + ''' of item ''' + str(index) + ''' of to dos of list "''' + list_name + '''"
        if theDate is missing value then
            return ""
        else
            set h to hours of theDate as integer
            set m to minutes of theDate as integer
            set mm to text -2 thru -1 of ("0" & m as string)
            return (h as string) & ":" & mm
        end if
    end tell
    '''
    raw_result = runAppleScript(script)
    return raw_result if raw_result else ""


def getTaskProject(index: int, list_name: str) -> str:
    """Get project name for a task by index from specified list."""
    project_script = '''
    tell application "Things3"
        set theTask to item ''' + str(index) + ''' of to dos of list "''' + list_name + '''"
        if project of theTask is not missing value then
            return name of project of theTask
        else
            return ""
        end if
    end tell
    '''
    project = runAppleScript(project_script)
    if not project:
        project = "None"
    return project


def processTaskBatch(task_indices: List[int], task_details_func, max_workers: int = 12) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel using the provided task details function."""
    tasks = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(task_indices))) as executor:
        future_to_index = {
            executor.submit(task_details_func, i): i 
            for i in task_indices
        }
        
        for future in as_completed(future_to_index):
            try:
                task = future.result()
                if task:  # Only include non-None tasks
                    tasks.append(task)
            except Exception as e:
                index = future_to_index[future]
                print("\nError processing task " + str(index) + ": " + str(e), file=sys.stderr)
    
    return tasks


def writeToCsv(tasks: List[Dict[str, str]], filename: str) -> None:
    """Write tasks to CSV file with consistent format compatible with import_google_tasks.py."""
    if not tasks:
        print("No tasks to write to CSV")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Create DataFrame with consistent column order (compatible with import_google_tasks.py)
    columns = ["ItemName", "ItemType", "ResidesWithin", "Notes", "ToDoDate", "DueDate", "DueTime", "Tags", "TaskID"]
    
    # Map task dict keys to CSV column names
    csv_data = []
    for task in tasks:
        # Split due_date into date and time if it contains time
        due_date = task.get("due_date", "")
        due_time = ""
        
        # Check if due_date contains time information
        if due_date and "T" in due_date:
            date_part, time_part = due_date.split("T", 1)
            due_date = date_part
            # Extract time without seconds/milliseconds
            if ":" in time_part:
                time_components = time_part.split(":")
                if len(time_components) >= 2:
                    due_time = time_components[0] + ":" + time_components[1]
        
        csv_row = {
            "ItemName": task.get("title", ""),
            "ItemType": "Task",
            "ResidesWithin": task.get("project", "None"),
            "Notes": task.get("notes", ""),
            "ToDoDate": task.get("start_date", ""),
            "DueDate": due_date,
            "DueTime": due_time,
            "Tags": task.get("tags", ""),
            "TaskID": task.get("task_id", "")
        }
        csv_data.append(csv_row)
    
    df = pd.DataFrame(csv_data, columns=columns)
    df.to_csv(filename, index=False, encoding='utf-8')
    print("Saved " + str(len(tasks)) + " tasks to " + filename) 
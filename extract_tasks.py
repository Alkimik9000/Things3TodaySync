#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Today tasks from Things3 using AppleScript and save to CSV.
This version uses a simpler approach to avoid AppleScript syntax issues.
"""

import subprocess
import csv
import sys
from typing import List, Dict
import re


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
        print(f"AppleScript error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def getTodayTaskCount() -> int:
    """Get count of tasks in Today view."""
    script = 'tell application "Things3" to count to dos of list "Today"'
    count_str = runAppleScript(script)
    return int(count_str)


def getTaskProperty(index: int, property_name: str) -> str:
    """Get a specific property of a task by index."""
    script = f'tell application "Things3" to {property_name} of item {index} of to dos of list "Today"'
    result = runAppleScript(script)
    # Handle missing values
    if result == "missing value":
        return ""
    return result


def getTaskTags(index: int) -> str:
    """Get tags for a task."""
    script = f'''
    tell application "Things3"
        set theTags to tags of item {index} of to dos of list "Today"
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


def formatDate(date_str: str) -> str:
    """Convert AppleScript date to YYYY-MM-DD format."""
    if not date_str:
        return ""
    
    # AppleScript returns dates like "Monday, June 10, 2025 at 12:00:00 AM"
    # Extract date components using regex
    match = re.search(r'(\w+), (\w+) (\d+), (\d{4})', date_str)
    if match:
        month_name = match.group(2)
        day = int(match.group(3))
        year = int(match.group(4))
        
        # Convert month name to number
        months = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        month = months.get(month_name, 1)
        
        return f"{year:04d}-{month:02d}-{day:02d}"
    return ""


def getTaskDetails(index: int) -> Dict[str, str]:
    """Get all details for a single task."""
    # Get basic properties
    title = getTaskProperty(index, "name")
    notes = getTaskProperty(index, "notes")
    
    # Get dates (use "activation date" instead of "start date")
    start_date_str = getTaskProperty(index, "activation date")
    due_date_str = getTaskProperty(index, "due date")
    
    # Get project
    project_script = f'''
    tell application "Things3"
        set theTask to item {index} of to dos of list "Today"
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
    
    # Get tags
    tags = getTaskTags(index)
    
    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": formatDate(start_date_str),
        "due_date": formatDate(due_date_str),
        "tags": tags
    }


def extractTodayTasks() -> List[Dict[str, str]]:
    """Extract all tasks from Today view."""
    task_count = getTodayTaskCount()
    print(f"Found {task_count} tasks in Today view")
    
    tasks = []
    for i in range(1, task_count + 1):
        print(f"Extracting task {i}/{task_count}...", end="\r")
        task = getTaskDetails(i)
        tasks.append(task)
    
    print()  # New line after progress
    return tasks


def writeToCsv(tasks: List[Dict[str, str]], filename: str = "today_view.csv"):
    """Write tasks to CSV file in the expected format."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["ItemName", "ItemType", "ResidesWithin", "Notes", "ToDoDate", "DueDate", "Tags"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in tasks:
            # Clean up notes - replace newlines with spaces
            notes = task["notes"].replace("\n", " ").replace("\r", " ")
            
            # Format row with proper escaping
            row = {
                "ItemName": '"' + task["title"].replace('"', '""') + '"',
                "ItemType": '"Task"',
                "ResidesWithin": '"' + task["project"].replace('"', '""') + '"',
                "Notes": '"' + notes.replace('"', '""') + '"' if notes else '""',
                "ToDoDate": '"' + task["start_date"] + '"' if task["start_date"] else '""',
                "DueDate": '"' + task["due_date"] + '"' if task["due_date"] else '""',
                "Tags": '"' + task["tags"].replace('"', '""') + '"' if task["tags"] else '""'
            }
            writer.writerow(row)


def main():
    """Main function."""
    print("Extracting Today tasks from Things3...")
    tasks = extractTodayTasks()
    writeToCsv(tasks)
    print(f"Successfully wrote {len(tasks)} tasks to today_view.csv")


if __name__ == "__main__":
    main()

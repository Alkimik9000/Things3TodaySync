#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Today tasks from Things3 using AppleScript and save to CSV.
This version uses a simpler approach to avoid AppleScript syntax issues.
"""

import subprocess
import pandas as pd
import os
import sys
import re
from typing import List, Dict

OUTPUT_DIR = "outputs"


_ENG_LETTER_RE = re.compile(r"[A-Za-z]")


def is_pure_english(text: str) -> bool:
    """Return True if ``text`` contains only ASCII characters and at least
    one English letter."""

    return bool(text) and text.isascii() and bool(_ENG_LETTER_RE.search(text))


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


def getFormattedDate(index: int, primary_prop: str, fallback_prop: str | None = None) -> str:
    """Return Things3 date property as YYYY-MM-DD or empty string.

    Uses AppleScript to extract year / month / day components directly so it
    works regardless of macOS locale.
    """
    script = f'''
    tell application "Things3"
        set theDate to {primary_prop} of item {index} of to dos of list "Today"
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
    if not raw_result and fallback_prop:
        # Try fallback AppleScript property
        script_fallback = script.replace(primary_prop, fallback_prop)
        raw_result = runAppleScript(script_fallback)
    if not raw_result:
        return ""
    try:
        y_str, m_str, d_str = [part.strip() for part in raw_result.split(",")]
        y, m, d = int(y_str), int(m_str), int(d_str)
        return ("%04d" % y) + "-" + ("%02d" % m) + "-" + ("%02d" % d)
    except ValueError:
        return ""


def getTaskDetails(index: int) -> Dict[str, str]:
    """Get all details for a single task."""
    # Get basic properties
    title = getTaskProperty(index, "name")
    notes = getTaskProperty(index, "notes")
    
    # Get dates using locale-independent ISO formatting
    start_date_str = getFormattedDate(index, "activation date")
    due_date_str = getFormattedDate(index, "due date", "deadline")
    
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
        "start_date": start_date_str,
        "due_date": due_date_str,
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
        if is_pure_english(task["title"]):
            print(f"Skipping English-only task: {task['title']}")
            continue
        tasks.append(task)
    
    print()  # New line after progress
    return tasks


def writeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, 'today_view.csv'),
) -> None:
    """Write tasks to CSV file using pandas."""

    rows = []
    for task in tasks:
        notes = task['notes'].replace('\n', ' ').replace('\r', ' ')
        rows.append({
            'ItemName': task['title'],
            'ItemType': 'Task',
            'ResidesWithin': task['project'],
            'Notes': notes,
            'ToDoDate': task['start_date'],
            'DueDate': task['due_date'],
            'Tags': task['tags'],
        })

    df = pd.DataFrame(rows, columns=[
        'ItemName',
        'ItemType',
        'ResidesWithin',
        'Notes',
        'ToDoDate',
        'DueDate',
        'Tags',
    ])

    df.to_csv(filename, index=False, quoting=1)

def main():
    """Main function."""
    print("Extracting Today tasks from Things3...")
    tasks = extractTodayTasks()
    writeToCsv(tasks)
    print(
        f"Successfully wrote {len(tasks)} tasks to {os.path.join(OUTPUT_DIR, 'today_view.csv')}"
    )


if __name__ == "__main__":
    main()

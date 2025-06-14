#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract tasks from the "Anytime" list in Things3 where both the start date and
``due date`` are not set. The extracted tasks are saved as
``outputs/anytime_tasks.csv`` with the same columns as the other CSV exports.
"""

import subprocess
import csv
import os
import sys
from typing import List, Dict

OUTPUT_DIR = "outputs"


def runAppleScript(script: str) -> str:
    """Execute AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"AppleScript error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def getAnytimeTaskCount() -> int:
    """Get count of tasks in the Anytime list."""
    script = 'tell application "Things3" to count to dos of list "Anytime"'
    count_str = runAppleScript(script)
    return int(count_str)


def getTaskProperty(index: int, property_name: str) -> str:
    """Get a specific property of a task by index."""
    script = (
        f'tell application "Things3" to {property_name} of item {index} of to dos of list "Anytime"'
    )
    result = runAppleScript(script)
    if result == "missing value":
        return ""
    return result


def getTaskTags(index: int) -> str:
    """Return a semicolon-separated list of tags for the task."""
    script = f'''
    tell application "Things3"
        set theTags to tags of item {index} of to dos of list "Anytime"
        set tagList to ""
        repeat with aTag in theTags
            set tagList to tagList & name of aTag & "; "
        end repeat
        return tagList
    end tell
    '''
    tags = runAppleScript(script).strip()
    if tags.endswith("; "):
        tags = tags[:-2]
    return tags


def getFormattedDate(index: int, property_name: str) -> str:
    """Return Things3 date property formatted as YYYY-MM-DD or empty string."""
    script = f'''
    tell application "Things3"
        set theDate to {property_name} of item {index} of to dos of list "Anytime"
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
        return f"{y:04d}-{m:02d}-{d:02d}"
    except ValueError:
        return ""


def getTaskDetails(index: int) -> Dict[str, str] | None:
    """Return a dictionary of task details or ``None`` if the task should be skipped."""
    title = getTaskProperty(index, "name")
    notes = getTaskProperty(index, "notes")

    start_date = getFormattedDate(index, "activation date")
    due_date = getFormattedDate(index, "due date") or getFormattedDate(index, "deadline")

    # Skip tasks that have either a start or due date
    if start_date or due_date:
        return None

    project_script = f'''
    tell application "Things3"
        set theTask to item {index} of to dos of list "Anytime"
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

    tags = getTaskTags(index)

    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": start_date,
        "due_date": due_date,
        "tags": tags,
    }


def extractAnytimeTasks() -> List[Dict[str, str]]:
    """Extract tasks from Anytime that lack both start and due dates."""
    task_count = getAnytimeTaskCount()
    print(f"Found {task_count} tasks in Anytime")

    tasks: List[Dict[str, str]] = []
    for i in range(1, task_count + 1):
        print(f"Processing task {i}/{task_count}...", end="\r")
        details = getTaskDetails(i)
        if details:
            tasks.append(details)

    print()
    return tasks


def writeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, "anytime_tasks.csv"),
) -> None:
    """Write the given tasks to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["ItemName", "ItemType", "ResidesWithin", "Notes", "ToDoDate", "DueDate", "Tags"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for task in tasks:
            notes = task["notes"].replace("\n", " ").replace("\r", " ")
            row = {
                "ItemName": '"' + task["title"].replace('"', '""') + '"',
                "ItemType": '"Task"',
                "ResidesWithin": '"' + task["project"].replace('"', '""') + '"',
                "Notes": '"' + notes.replace('"', '""') + '"' if notes else '""',
                "ToDoDate": '"' + task["start_date"] + '"' if task["start_date"] else '""',
                "DueDate": '"' + task["due_date"] + '"' if task["due_date"] else '""',
                "Tags": '"' + task["tags"].replace('"', '""') + '"' if task["tags"] else '""',
            }
            writer.writerow(row)


def main() -> None:
    print("Extracting Anytime tasks from Things3...")
    tasks = extractAnytimeTasks()
    writeToCsv(tasks)
    print(
        f"Successfully wrote {len(tasks)} tasks to {os.path.join(OUTPUT_DIR, 'anytime_tasks.csv')}"
    )


if __name__ == "__main__":
    main()

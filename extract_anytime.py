#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract tasks from the "Anytime" list in Things3 where both the start date and
``due date`` are not set. The extracted tasks are saved as
``outputs/anytime_tasks.csv`` with the same columns as the other CSV exports.
"""

import subprocess
import pandas as pd
import os
import sys
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
MAX_WORKERS = 12  # Number of concurrent AppleScript processes
BATCH_SIZE = 10   # Number of tasks to process in each batch


def canon_title(title: str) -> str:
    """Return a canonical representation of ``title`` for comparison."""
    return " ".join(title.strip().split()).lower()


def load_existing_titles(csv_file: str) -> set[str]:
    """Return a set of canonical titles from ``csv_file`` if it exists."""
    if not os.path.exists(csv_file):
        return set()
    df = pd.read_csv(csv_file)
    return {canon_title(str(t)) for t in df.get("ItemName", [])}

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


def getTaskUUID(index: int) -> str:
    script = f'tell application "Things3" to id of item {index} of to dos of list "Anytime"'
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
        return "%04d" % y + "-" + "%02d" % m + "-" + "%02d" % d
    except ValueError:
        return ""


def getTaskDetails(index: int) -> Dict[str, str] | None:
    """Return a dictionary of task details or ``None`` if the task should be skipped."""
    title = getTaskProperty(index, "name")
    notes = getTaskProperty(index, "notes")
    uuid = getTaskUUID(index)

    start_date = getFormattedDate(index, "activation date")
    due_date = getFormattedDate(index, "due date")

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
        "task_id": uuid
    }


def process_task_batch(task_indices: List[int]) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel."""
    tasks = []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(task_indices))) as executor:
        future_to_index = {
            executor.submit(getTaskDetails, i): i 
            for i in task_indices
        }
        
        for future in as_completed(future_to_index):
            try:
                task = future.result()
                if task:  # Only include tasks without dates
                    tasks.append(task)
            except Exception as e:
                index = future_to_index[future]
                print(f"\nError processing task {index}: {e}", file=sys.stderr)
    
    return tasks


def extractAnytimeTasks() -> List[Dict[str, str]]:
    """Extract tasks from Anytime that lack both start and due dates using parallel processing."""
    task_count = getAnytimeTaskCount()
    if task_count == 0:
        print("No tasks found in Anytime")
        return []
    
    print(f"Found {task_count} tasks in Anytime")
    print(f"Processing in batches of {BATCH_SIZE} with {MAX_WORKERS} workers...")

    all_tasks = []
    start_time = time.time()
    
    # Process tasks in batches
    for batch_start in range(1, task_count + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, task_count + 1)
        batch_indices = list(range(batch_start, batch_end))
        
        print(f"Processing tasks {batch_start}-{batch_end-1} of {task_count}...")
        
        # Process batch
        batch_tasks = process_task_batch(batch_indices)
        all_tasks.extend(batch_tasks)
        
        # Estimate time remaining
        elapsed = time.time() - start_time
        tasks_done = batch_end - 1
        if tasks_done > 0:
            time_per_task = elapsed / tasks_done
            remaining = (task_count - tasks_done) * time_per_task
            print(f"  Processed {tasks_done}/{task_count} tasks "
                  f"({tasks_done/task_count:.0%}), "
                  f"ETA: {remaining:.1f} seconds remaining")

    print(f"\nCompleted processing {len(all_tasks)} tasks in {time.time() - start_time:.1f} seconds")
    
    # Filter duplicates from other lists
    today_csv = os.path.join(OUTPUT_DIR, "today_view.csv")
    upcoming_csv = os.path.join(OUTPUT_DIR, "upcoming_tasks.csv")
    existing = load_existing_titles(today_csv) | load_existing_titles(upcoming_csv)
    filtered = []
    for t in all_tasks:
        if canon_title(t["title"]) in existing:
            print(f"Skipping duplicate from other lists: {t['title']}")
            continue
        filtered.append(t)
    return filtered


def writeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, "anytime_tasks.csv"),
) -> None:
    """Write the given tasks to a CSV file using pandas."""

    rows = []
    for task in tasks:
        notes = task["notes"].replace("\n", " ").replace("\r", " ")
        rows.append(
            {
                "ItemName": task["title"],
                "ItemType": "Task",
                "ResidesWithin": task["project"],
                "Notes": notes,
                "ToDoDate": task["start_date"],
                "DueDate": task["due_date"],
                "Tags": task["tags"],
                "TaskID": task["task_id"],
            }
        )

    df = pd.DataFrame(rows, columns=[
        "ItemName",
        "ItemType",
        "ResidesWithin",
        "Notes",
        "ToDoDate",
        "DueDate",
        "Tags",
        "TaskID",
    ])

    df.to_csv(filename, index=False, quoting=1)


def main() -> None:
    print("Extracting Anytime tasks from Things3...")
    tasks = extractAnytimeTasks()
    writeToCsv(tasks)
    print(
        f"Successfully wrote {len(tasks)} tasks to {os.path.join(OUTPUT_DIR, 'anytime_tasks.csv')}"
    )


if __name__ == "__main__":
    main()

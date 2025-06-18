#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Upcoming tasks from Things3 using AppleScript and save to CSV.
This version uses parallel processing to improve performance.
"""

import subprocess
import pandas as pd
import os
import sys
import time
from typing import List, Dict


def canon_title(title: str) -> str:
    """Return a canonical representation of ``title`` for comparison."""
    return " ".join(title.strip().split()).lower()
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
MAX_WORKERS = 12  # Number of concurrent AppleScript processes
BATCH_SIZE = 10   # Number of tasks to process in each batch

OUTPUT_DIR = "outputs"


def load_existing_titles(csv_file: str) -> set[str]:
    """Return a set of canonical titles from ``csv_file`` if it exists."""
    if not os.path.exists(csv_file):
        return set()
    df = pd.read_csv(csv_file)
    return {canon_title(str(t)) for t in df.get("ItemName", [])}



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


def getUpcomingTaskCount() -> int:
    """Get count of tasks in the Upcoming list."""
    script = 'tell application "Things3" to count to dos of list "Upcoming"'
    count_str = runAppleScript(script)
    return int(count_str)


def getTaskProperty(index: int, property_name: str) -> str:
    """Get a specific property of a task by index."""
    script = f'tell application "Things3" to {property_name} of item {index} of to dos of list "Upcoming"'
    result = runAppleScript(script)
    # Handle missing values
    if result == "missing value":
        return ""
    return result


def getTaskUUID(index: int) -> str:
    script = f'tell application "Things3" to id of item {index} of to dos of list "Upcoming"'
    result = runAppleScript(script)
    if result == "missing value":
        return ""
    return result


def getTaskTags(index: int) -> str:
    """Get tags for a task."""
    script = f'''
    tell application "Things3"
        set theTags to tags of item {index} of to dos of list "Upcoming"
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
        set theDate to {primary_prop} of item {index} of to dos of list "Upcoming"
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
    if (not raw_result or raw_result == "") and fallback_prop:
        # Try fallback AppleScript property
        script_fallback = f'''
        tell application "Things3"
            set theDate to {fallback_prop} of item {index} of to dos of list "Upcoming"
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
    uuid = getTaskUUID(index)
    
    # Get dates using locale-independent ISO formatting
    start_date_str = getFormattedDate(index, "activation date")
    due_date_str = getFormattedDate(index, "due date")  # Only use 'due date', no fallback
    
    # Get project
    project_script = f'''
    tell application "Things3"
        set theTask to item {index} of to dos of list "Upcoming"
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
                tasks.append(task)
            except Exception as e:
                index = future_to_index[future]
                print(f"\nError processing task {index}: {e}", file=sys.stderr)
    
    return tasks

def extractUpcomingTasks() -> List[Dict[str, str]]:
    """Extract all tasks from the Upcoming list using parallel processing."""
    task_count = getUpcomingTaskCount()
    if task_count == 0:
        print("No tasks found in Upcoming")
        return []
    
    print(f"Found {task_count} tasks in Upcoming")
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
        tasks_done = len(all_tasks)
        if tasks_done > 0:
            time_per_task = elapsed / tasks_done
            remaining = (task_count - tasks_done) * time_per_task
            print(f"  Processed {tasks_done}/{task_count} tasks "
                  f"({tasks_done/task_count:.0%}), "
                  f"ETA: {remaining/60:.1f} minutes remaining")
    
    print(f"\nCompleted processing {len(all_tasks)} tasks in {time.time() - start_time:.1f} seconds")
    today_csv = os.path.join(OUTPUT_DIR, 'today_view.csv')
    existing_titles = load_existing_titles(today_csv)
    filtered = []
    for t in all_tasks:
        if canon_title(t['title']) in existing_titles:
            print(f"Skipping duplicate in Today: {t['title']}")
            continue
        filtered.append(t)
    return filtered


def writeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, 'upcoming_tasks.csv'),
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
            'TaskID': task['task_id'],
        })

    df = pd.DataFrame(rows, columns=[
        'ItemName',
        'ItemType',
        'ResidesWithin',
        'Notes',
        'ToDoDate',
        'DueDate',
        'Tags',
        'TaskID',
    ])

    df.to_csv(filename, index=False, quoting=1)

def main():
    """Main function with error handling and timing."""
    try:
        print("Extracting Upcoming tasks from Things3...")
        start_time = time.time()
        
        tasks = extractUpcomingTasks()
        if not tasks:
            print("No tasks to process.")
            return
            
        writeToCsv(tasks)

        elapsed = time.time() - start_time
        print(
            f"\n✅ Successfully wrote {len(tasks)} tasks to {os.path.join(OUTPUT_DIR, 'upcoming_tasks.csv')}"
        )
        print(f"Total processing time: {elapsed:.2f} seconds")
        print(f"Average time per task: {elapsed/len(tasks):.3f} seconds")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

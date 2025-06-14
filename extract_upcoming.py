#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Upcoming tasks from Things3 using AppleScript and save to CSV.
This version uses parallel processing to improve performance.
"""

import subprocess
import csv
import os
import sys
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
MAX_WORKERS = 12  # Number of concurrent AppleScript processes
BATCH_SIZE = 10   # Number of tasks to process in each batch

OUTPUT_DIR = "outputs"



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
        "tags": tags
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
    return all_tasks


def writeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, "upcoming_tasks.csv"),
) -> None:
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

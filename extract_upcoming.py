#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Upcoming tasks from Things3 using AppleScript and save to CSV.
This version uses parallel processing to improve performance.
"""

import os
import sys
import time
from typing import List, Dict

from utils import (
    runAppleScript, getTaskCount, getTaskProperty, getTaskUUID, getTaskTags,
    getFormattedDate, getTaskProject, processTaskBatch, writeToCsv, canonTitle, loadExistingTitles
)

# Configuration
MAX_WORKERS = 12  # Number of concurrent AppleScript processes
BATCH_SIZE = 10   # Number of tasks to process in each batch

OUTPUT_DIR = "outputs"


def getUpcomingTaskCount() -> int:
    """Get count of tasks in the Upcoming list."""
    return getTaskCount("Upcoming")


def getTaskPropertyUpcoming(index: int, property_name: str) -> str:
    """Get a specific property of a task by index from Upcoming list."""
    return getTaskProperty(index, property_name, "Upcoming")


def getTaskUUIDUpcoming(index: int) -> str:
    """Get UUID of a task by index from Upcoming list."""
    return getTaskUUID(index, "Upcoming")


def getTaskTagsUpcoming(index: int) -> str:
    """Get tags for a task from Upcoming list."""
    return getTaskTags(index, "Upcoming")


def getFormattedDateUpcoming(index: int, primary_prop: str, fallback_prop: str | None = None) -> str:
    """Return Things3 date property as YYYY-MM-DD or empty string with fallback support."""
    result = getFormattedDate(index, primary_prop, "Upcoming")
    if (not result or result == "") and fallback_prop:
        result = getFormattedDate(index, fallback_prop, "Upcoming")
    return result


def getTaskDetails(index: int) -> Dict[str, str]:
    """Get all details for a single task."""
    # Get basic properties
    title = getTaskPropertyUpcoming(index, "name")
    notes = getTaskPropertyUpcoming(index, "notes")
    uuid = getTaskUUIDUpcoming(index)
    
    # Get dates using locale-independent ISO formatting
    start_date_str = getFormattedDateUpcoming(index, "activation date")
    due_date_str = getFormattedDateUpcoming(index, "due date")  # Only use 'due date', no fallback
    
    # Get project
    project = getTaskProject(index, "Upcoming")
    
    # Get tags
    tags = getTaskTagsUpcoming(index)
    
    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": start_date_str,
        "due_date": due_date_str,
        "tags": tags,
        "task_id": uuid
    }


def process_task_batch_upcoming(task_indices: List[int]) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel."""
    return processTaskBatch(task_indices, getTaskDetails, MAX_WORKERS)

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
        batch_tasks = process_task_batch_upcoming(batch_indices)
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
    existing_titles = loadExistingTitles(today_csv)
    filtered = []
    for t in all_tasks:
        if canonTitle(t['title']) in existing_titles:
            print("Skipping duplicate in Today: " + t['title'])
            continue
        filtered.append(t)
    return filtered


def writeUpcomingToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, 'upcoming_tasks.csv'),
) -> None:
    """Write tasks to CSV file with consistent format."""
    # Convert to format expected by import_google_tasks.py
    for task in tasks:
        if 'notes' in task:
            task['notes'] = task['notes'].replace('\n', ' ').replace('\r', ' ')
    
    writeToCsv(tasks, filename)

def main():
    """Main function with error handling and timing."""
    try:
        print("Extracting Upcoming tasks from Things3...")
        start_time = time.time()
        
        tasks = extractUpcomingTasks()
        if not tasks:
            print("No tasks to process.")
            return
            
        writeUpcomingToCsv(tasks)

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

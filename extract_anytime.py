#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract tasks from the "Anytime" list in Things3 where both the start date and
``due date`` are not set. The extracted tasks are saved as
``outputs/anytime_tasks.csv`` with the same columns as the other CSV exports.
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


def getAnytimeTaskCount() -> int:
    """Get count of tasks in the Anytime list."""
    return getTaskCount("Anytime")


def getTaskPropertyAnytime(index: int, property_name: str) -> str:
    """Get a specific property of a task by index from Anytime list."""
    return getTaskProperty(index, property_name, "Anytime")


def getTaskUUIDAnytime(index: int) -> str:
    """Get UUID of a task by index from Anytime list."""
    return getTaskUUID(index, "Anytime")


def getTaskTagsAnytime(index: int) -> str:
    """Get tags for a task from Anytime list."""
    return getTaskTags(index, "Anytime")


def getFormattedDateAnytime(index: int, property_name: str) -> str:
    """Return Things3 date property formatted as YYYY-MM-DD or empty string."""
    return getFormattedDate(index, property_name, "Anytime")


def getTaskDetails(index: int) -> Dict[str, str] | None:
    """Return a dictionary of task details or ``None`` if the task should be skipped."""
    title = getTaskPropertyAnytime(index, "name")
    notes = getTaskPropertyAnytime(index, "notes")
    uuid = getTaskUUIDAnytime(index)

    start_date = getFormattedDateAnytime(index, "activation date")
    due_date = getFormattedDateAnytime(index, "due date")

    # Skip tasks that have either a start or due date
    if start_date or due_date:
        return None

    # Get project
    project = getTaskProject(index, "Anytime")

    tags = getTaskTagsAnytime(index)

    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": start_date,
        "due_date": due_date,
        "tags": tags,
        "task_id": uuid
    }


def process_task_batch_anytime(task_indices: List[int]) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel."""
    return processTaskBatch(task_indices, getTaskDetails, MAX_WORKERS)


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
        batch_tasks = process_task_batch_anytime(batch_indices)
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
    existing = loadExistingTitles(today_csv) | loadExistingTitles(upcoming_csv)
    filtered = []
    for t in all_tasks:
        if canonTitle(t["title"]) in existing:
            print("Skipping duplicate from other lists: " + t['title'])
            continue
        filtered.append(t)
    return filtered


def writeAnytimeToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, "anytime_tasks.csv"),
) -> None:
    """Write tasks to CSV file with consistent format."""
    # Clean up notes formatting
    for task in tasks:
        if 'notes' in task:
            task['notes'] = task['notes'].replace('\n', ' ').replace('\r', ' ')
    
    writeToCsv(tasks, filename)


def main() -> None:
    print("Extracting Anytime tasks from Things3...")
    tasks = extractAnytimeTasks()
    writeAnytimeToCsv(tasks)
    print(
        f"Successfully wrote {len(tasks)} tasks to {os.path.join(OUTPUT_DIR, 'anytime_tasks.csv')}"
    )


if __name__ == "__main__":
    main()

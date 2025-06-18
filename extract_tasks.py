#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Today tasks from Things3 using AppleScript and save to CSV.
This version uses a simpler approach to avoid AppleScript syntax issues.
"""

import os
import sys
import re
import time
from typing import List, Dict

from utils import (
    runAppleScript, getTaskCount, getTaskProperty, getTaskUUID, getTaskTags,
    getFormattedDate, getFormattedTime, getTaskProject, processTaskBatch, writeToCsv
)

# Configuration
MAX_WORKERS = 12  # Number of concurrent AppleScript processes
BATCH_SIZE = 10   # Number of tasks to process in each batch

OUTPUT_DIR = "outputs"


_ENG_LETTER_RE = re.compile(r"[A-Za-z]")


def is_pure_english(text: str) -> bool:
    """Return True if ``text`` contains only ASCII characters and at least
    one English letter."""

    return bool(text) and text.isascii() and bool(_ENG_LETTER_RE.search(text))


def getTodayTaskCount() -> int:
    """Get count of tasks in Today view."""
    return getTaskCount("Today")


def getTaskPropertyToday(index: int, property_name: str) -> str:
    """Get a specific property of a task by index from Today list."""
    return getTaskProperty(index, property_name, "Today")


def getTaskUUIDToday(index: int) -> str:
    """Get UUID of a task by index from Today list."""
    return getTaskUUID(index, "Today")


def getTaskTagsToday(index: int) -> str:
    """Get tags for a task from Today list."""
    return getTaskTags(index, "Today")


def getFormattedDateToday(index: int, primary_prop: str, fallback_prop: str | None = None) -> str:
    """Return Things3 date property as YYYY-MM-DD or empty string with fallback support."""
    result = getFormattedDate(index, primary_prop, "Today")
    if (not result or result == "") and fallback_prop:
        result = getFormattedDate(index, fallback_prop, "Today")
    return result


def getFormattedTimeToday(index: int, primary_prop: str, fallback_prop: str | None = None) -> str:
    """Return Things3 time component as HH:MM or empty string with fallback support."""
    result = getFormattedTime(index, primary_prop, "Today")
    if (not result or result == "") and fallback_prop:
        result = getFormattedTime(index, fallback_prop, "Today")
    return result


def getTaskDetails(index: int) -> Dict[str, str]:
    """Get all details for a single task."""
    # Get basic properties
    title = getTaskPropertyToday(index, "name")
    notes = getTaskPropertyToday(index, "notes")
    uuid = getTaskUUIDToday(index)
    
    # Get dates using locale-independent ISO formatting
    start_date_str = getFormattedDateToday(index, "activation date")
    due_date_str = getFormattedDateToday(index, "due date")
    due_time_str = getFormattedTimeToday(index, "due date")
    
    # Get project
    project = getTaskProject(index, "Today")
    
    # Get tags
    tags = getTaskTagsToday(index)
    
    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": start_date_str,
        "due_date": due_date_str,
        "due_time": due_time_str,
        "tags": tags,
        "task_id": uuid
    }


def process_task_batch_today(task_indices: List[int]) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel, filtering out English-only tasks."""
    def filtered_task_details(index: int) -> Dict[str, str] | None:
        task = getTaskDetails(index)
        if task and not is_pure_english(task["title"]):
            return task
        elif task:
            print("Skipping English-only task: " + task["title"])
        return None
    
    return processTaskBatch(task_indices, filtered_task_details, MAX_WORKERS)


def extractTodayTasks() -> List[Dict[str, str]]:
    """Extract all tasks from Today view using parallel processing."""
    task_count = getTodayTaskCount()
    if task_count == 0:
        print("No tasks found in Today")
        return []
    
    print(f"Found {task_count} tasks in Today view")
    print(f"Processing in batches of {BATCH_SIZE} with {MAX_WORKERS} workers...")
    
    all_tasks = []
    start_time = time.time()
    
    # Process tasks in batches
    for batch_start in range(1, task_count + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, task_count + 1)
        batch_indices = list(range(batch_start, batch_end))
        
        print(f"Processing tasks {batch_start}-{batch_end-1} of {task_count}...")
        
        # Process batch
        batch_tasks = process_task_batch_today(batch_indices)
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
    return all_tasks


def writeTodayToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, 'today_view.csv'),
) -> None:
    """Write tasks to CSV file with Today-specific format."""
    # Convert to format expected by import_google_tasks.py
    for task in tasks:
        if 'notes' in task:
            task['notes'] = task['notes'].replace('\n', ' ').replace('\r', ' ')
        # Combine due_date and due_time if both exist
        if task.get('due_time') and task.get('due_date'):
            task['due_date'] = task['due_date'] + 'T' + task['due_time'] + ':00'
    
    writeToCsv(tasks, filename)

def main():
    """Main function."""
    print("Extracting Today tasks from Things3...")
    tasks = extractTodayTasks()
    writeTodayToCsv(tasks)
    print(
        "Successfully wrote " + str(len(tasks)) + " tasks to " + os.path.join(OUTPUT_DIR, 'today_view.csv')
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Someday tasks from Things3 using AppleScript and save to CSV.
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


def getSomedayTaskCount() -> int:
    """Get count of tasks in the Someday list."""
    return getTaskCount("Someday")


def getTaskPropertySomeday(index: int, property_name: str) -> str:
    """Get a specific property of a task by index from Someday list."""
    return getTaskProperty(index, property_name, "Someday")


def getTaskUUIDSomeday(index: int) -> str:
    """Get UUID of a task by index from Someday list."""
    return getTaskUUID(index, "Someday")


def getTaskTagsSomeday(index: int) -> str:
    """Get tags for a task from Someday list."""
    return getTaskTags(index, "Someday")


def getFormattedDateSomeday(index: int, property_name: str) -> str:
    """Return Things3 date property formatted as YYYY-MM-DD or empty string."""
    return getFormattedDate(index, property_name, "Someday")


def getTaskDetails(index: int) -> Dict[str, str]:
    """Get all details for a single task."""
    # Get basic properties
    title = getTaskPropertySomeday(index, "name")
    notes = getTaskPropertySomeday(index, "notes")
    uuid = getTaskUUIDSomeday(index)
    
    # Get dates using locale-independent ISO formatting
    start_date_str = getFormattedDateSomeday(index, "activation date")
    due_date_str = getFormattedDateSomeday(index, "due date")
    
    # Get project
    project = getTaskProject(index, "Someday")
    
    # Get tags
    tags = getTaskTagsSomeday(index)
    
    return {
        "title": title,
        "notes": notes,
        "project": project,
        "start_date": start_date_str,
        "due_date": due_date_str,
        "tags": tags,
        "task_id": uuid
    }


def process_task_batch_someday(task_indices: List[int]) -> List[Dict[str, str]]:
    """Process a batch of tasks in parallel."""
    return processTaskBatch(task_indices, getTaskDetails, MAX_WORKERS)


def extractSomedayTasks() -> List[Dict[str, str]]:
    """Extract all tasks from the Someday list using parallel processing."""
    task_count = getSomedayTaskCount()
    if task_count == 0:
        print("No tasks found in Someday")
        return []
    
    print("Found " + str(task_count) + " tasks in Someday")
    print("Processing in batches of " + str(BATCH_SIZE) + " with " + str(MAX_WORKERS) + " workers...")
    
    all_tasks = []
    start_time = time.time()
    
    # Process tasks in batches
    for batch_start in range(1, task_count + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, task_count + 1)
        batch_indices = list(range(batch_start, batch_end))
        
        print("Processing tasks " + str(batch_start) + "-" + str(batch_end-1) + " of " + str(task_count) + "...")
        
        # Process batch
        batch_tasks = process_task_batch_someday(batch_indices)
        all_tasks.extend(batch_tasks)
        
        # Estimate time remaining
        elapsed = time.time() - start_time
        tasks_done = len(all_tasks)
        if tasks_done > 0:
            time_per_task = elapsed / tasks_done
            remaining = (task_count - tasks_done) * time_per_task
            print("  Processed " + str(tasks_done) + "/" + str(task_count) + " tasks " +
                  "(" + str(int(tasks_done/task_count*100)) + "%), " +
                  "ETA: " + str(remaining/60) + " minutes remaining")
    
    print("\nCompleted processing " + str(len(all_tasks)) + " tasks in " + str(time.time() - start_time) + " seconds")
    
    # Filter duplicates from other lists
    today_csv = os.path.join(OUTPUT_DIR, 'today_view.csv')
    upcoming_csv = os.path.join(OUTPUT_DIR, 'upcoming_tasks.csv')
    anytime_csv = os.path.join(OUTPUT_DIR, 'anytime_tasks.csv')
    
    existing = (loadExistingTitles(today_csv) | 
                loadExistingTitles(upcoming_csv) | 
                loadExistingTitles(anytime_csv))
    
    filtered = []
    for t in all_tasks:
        if canonTitle(t['title']) in existing:
            print("Skipping duplicate from other lists: " + t['title'])
            continue
        filtered.append(t)
    
    return filtered


def writeSomedayToCsv(
    tasks: List[Dict[str, str]],
    filename: str = os.path.join(OUTPUT_DIR, 'someday_tasks.csv'),
) -> None:
    """Write tasks to CSV file with consistent format."""
    writeToCsv(tasks, filename)


def main():
    """Main function."""
    print("Extracting Someday tasks from Things3...")
    tasks = extractSomedayTasks()
    writeSomedayToCsv(tasks)
    print(
        "Successfully wrote " + str(len(tasks)) + " tasks to " + os.path.join(OUTPUT_DIR, 'someday_tasks.csv')
    )


if __name__ == "__main__":
    main() 
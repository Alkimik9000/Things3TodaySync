#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract Someday tasks from Things3 using AppleScript and save to CSV.
This version extracts ALL tasks without activation date (true someday tasks).
"""

import os
import sys
import time
from typing import List, Dict
import pandas as pd

from utils import runAppleScript, writeToCsv, canonTitle, loadExistingTitles

OUTPUT_DIR = "outputs"


def extractAllSomedayTasks() -> List[Dict[str, str]]:
    """Extract all tasks without activation date using a single AppleScript call."""
    script = '''
    tell application "Things3"
        set output to ""
        set taskCount to 0
        
        repeat with toDo in to dos
            if status of toDo is open and activation date of toDo is missing value then
                set taskCount to taskCount + 1
                
                -- Get task properties
                set taskName to name of toDo
                set taskNotes to notes of toDo
                if taskNotes is missing value then set taskNotes to ""
                set taskID to id of toDo
                
                -- Get due date
                set taskDueDate to ""
                if due date of toDo is not missing value then
                    set d to due date of toDo
                    set taskDueDate to (year of d as string) & "-" & text -2 thru -1 of ("0" & (month of d as integer)) & "-" & text -2 thru -1 of ("0" & day of d)
                end if
                
                -- Get project
                set taskProject to "None"
                if project of toDo is not missing value then
                    set taskProject to name of project of toDo
                end if
                
                -- Get tags
                set taskTags to ""
                repeat with aTag in tags of toDo
                    set taskTags to taskTags & name of aTag & "; "
                end repeat
                if taskTags ends with "; " then set taskTags to text 1 thru -3 of taskTags
                
                -- Build output line
                set output to output & taskName & "|FIELD|" & taskNotes & "|FIELD|" & taskProject & "|FIELD|" & taskDueDate & "|FIELD|" & taskTags & "|FIELD|" & taskID & "|LINE|"
            end if
        end repeat
        
        return output & "|COUNT|" & taskCount
    end tell
    '''
    
    print("Extracting all someday tasks (without activation date)...")
    result = runAppleScript(script)
    
    if not result:
        print("No someday tasks found")
        return []
    
    # Parse the result
    parts = result.split("|COUNT|")
    if len(parts) != 2:
        print("Error parsing AppleScript result")
        return []
    
    data_part = parts[0]
    count = int(parts[1])
    
    print("Found " + str(count) + " someday tasks")
    
    # Parse tasks
    tasks = []
    lines = data_part.split("|LINE|")
    for line in lines:
        if not line.strip():
            continue
        
        fields = line.split("|FIELD|")
        if len(fields) >= 6:
            task = {
                "title": fields[0],
                "notes": fields[1],
                "project": fields[2],
                "start_date": "",  # Someday tasks don't have start dates
                "due_date": fields[3],
                "tags": fields[4],
                "task_id": fields[5]
            }
            tasks.append(task)
    
    print("Parsed " + str(len(tasks)) + " tasks")
    
    # Filter duplicates from other lists using TaskIDs
    today_csv = os.path.join(OUTPUT_DIR, 'today_view.csv')
    upcoming_csv = os.path.join(OUTPUT_DIR, 'upcoming_tasks.csv')
    anytime_csv = os.path.join(OUTPUT_DIR, 'anytime_tasks.csv')
    
    # Load existing TaskIDs
    existing_task_ids = set()
    for csv_file in [today_csv, upcoming_csv, anytime_csv]:
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            df = df.fillna('')
            existing_task_ids.update(str(task_id) for task_id in df.get("TaskID", []) if task_id)
    
    # Also check by canonical titles as fallback
    existing_titles = (loadExistingTitles(today_csv) | 
                      loadExistingTitles(upcoming_csv) | 
                      loadExistingTitles(anytime_csv))
    
    filtered = []
    skipped_count = 0
    for t in tasks:
        # Skip if TaskID exists in other lists
        if t.get('task_id') and t['task_id'] in existing_task_ids:
            print("Skipping duplicate (by TaskID) from other lists: " + t['title'])
            skipped_count += 1
            continue
        # Also skip if title matches (fallback for tasks without IDs)
        if canonTitle(t['title']) in existing_titles:
            print("Skipping duplicate (by title) from other lists: " + t['title'])
            skipped_count += 1
            continue
        filtered.append(t)
    
    print("\nFiltered out " + str(skipped_count) + " duplicates, keeping " + str(len(filtered)) + " unique Someday tasks")
    
    return filtered


def main():
    """Main function."""
    print("Extracting Someday tasks from Things3...")
    tasks = extractAllSomedayTasks()
    
    filename = os.path.join(OUTPUT_DIR, 'someday_tasks.csv')
    writeToCsv(tasks, filename)
    
    print("Successfully wrote " + str(len(tasks)) + " tasks to " + filename)


if __name__ == "__main__":
    main() 
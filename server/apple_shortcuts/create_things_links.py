#!/usr/bin/env python3
"""Generate Things3 URL links from ``processed_tasks.csv``.

This script lives in ``server/apple_shortcuts`` and reads tasks from a
``processed_tasks.csv`` file. It adds a "GenUrl" column with generated Things3
URLs and a "Processed" column to track which URLs have been fetched by iOS devices.

Each generated link pre-populates a Things task with the title, notes and
deadline from the CSV and schedules it for *Today*.
"""

from __future__ import annotations

import csv
import urllib.parse
from pathlib import Path
from typing import Dict, List
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR.parent / "outputs" / "processed_tasks.csv"
STATE_FILE = BASE_DIR / "last_linked_task.txt"
OUTPUT_FILE = BASE_DIR / "generated_things_urls.txt"


def read_last_processed() -> int:
    """Return the last processed task number."""
    if not STATE_FILE.exists():
        return 0
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return int(content) if content else 0


def write_last_processed(num: int) -> None:
    """Update the state file with ``num``."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(str(num))


def build_url(title: str, notes: str, due: str) -> str:
    """Return a Things URL to create a task for Today with optional deadline."""
    params = {"title": title, "when": "today"}
    if notes:
        params["notes"] = notes
    if due:
        # Convert ISO format (2025-06-15T00:00:00.000Z) to YYYY-MM-DD
        if "T" in due:
            due = due.split("T")[0]
        params["deadline"] = due
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"things:///add?{query}"


def update_csv_with_urls() -> None:
    """Update the CSV file with GenUrl and Processed columns."""
    if not CSV_FILE.exists():
        print("CSV file not found")
        return
    
    # Read the CSV using pandas
    df = pd.read_csv(CSV_FILE)
    
    # Add GenUrl and Processed columns if they don't exist
    if 'GenUrl' not in df.columns:
        df['GenUrl'] = ''
    if 'Processed' not in df.columns:
        df['Processed'] = 'No'
    
    # Get the last processed task number
    last_num = read_last_processed()
    
    # Track if we processed any new tasks
    processed_any = False
    max_num = last_num
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            task_num = int(row.get('TaskNumber', 0))
        except (ValueError, TypeError):
            continue
            
        # Only process new tasks (those with TaskNumber > last_num)
        if task_num > last_num and pd.isna(row.get('GenUrl')) or row.get('GenUrl') == '':
            title = str(row.get('TaskTitle', ''))
            notes = str(row.get('TaskNotes', ''))
            due = str(row.get('DueDate', ''))
            
            # Handle NaN values
            if pd.isna(notes) or notes == 'nan':
                notes = ''
            if pd.isna(due) or due == 'nan':
                due = ''
            
            # Generate the URL
            url = build_url(title, notes, due)
            
            # Update the DataFrame
            df.at[idx, 'GenUrl'] = url
            df.at[idx, 'Processed'] = 'No'
            
            # Also append to the legacy output file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(url + "\n")
            
            print(f"Generated URL for task {task_num}: {url}")
            processed_any = True
            
            if task_num > max_num:
                max_num = task_num
    
    # Save the updated CSV
    df.to_csv(CSV_FILE, index=False)
    
    # Update the state file with the highest processed task number
    if max_num > last_num:
        write_last_processed(max_num)
    
    if not processed_any:
        print("No new tasks to process")


def main() -> None:
    """Main function to update CSV with URLs."""
    update_csv_with_urls()


if __name__ == "__main__":
    main()

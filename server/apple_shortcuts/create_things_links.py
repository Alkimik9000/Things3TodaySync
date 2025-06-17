#!/usr/bin/env python3
"""Generate Things3 URL links from ``processed_tasks.csv``.

This script lives in ``server/apple_shortcuts`` and reads tasks from a
``processed_tasks.csv`` file in the same directory. Only entries with a
``TaskNumber`` higher than the value stored in ``last_linked_task.txt`` are
processed. Each new URL is appended to ``generated_things_urls.txt`` and printed
to stdout.

Each generated link pre-populates a Things task with the title, notes and
deadline from the CSV and schedules it for *Today*.
"""

from __future__ import annotations

import csv
import urllib.parse
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "processed_tasks.csv"
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


def load_new_rows() -> List[Dict[str, str]]:
    """Return rows from CSV with TaskNumber greater than the stored value."""
    last_num = read_last_processed()
    rows: List[Dict[str, str]] = []
    if not CSV_FILE.exists():
        return rows
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                num = int(row.get("TaskNumber", "0"))
            except ValueError:
                continue
            if num > last_num:
                rows.append(row)
    return rows


def build_url(title: str, notes: str, due: str) -> str:
    """Return a Things URL to create a task for Today."""
    params = {"title": title, "when": "today"}
    if notes:
        params["notes"] = notes
    if due:
        params["deadline"] = due
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"things:///add?{query}"


def main() -> None:
    rows = load_new_rows()
    if not rows:
        print("No new tasks to process")
        return

    max_num = 0
    urls: List[str] = []
    for row in rows:
        try:
            num = int(row.get("TaskNumber", "0"))
        except ValueError:
            continue
        title = row.get("TaskTitle", "")
        notes = row.get("TaskNotes", "")
        due = row.get("DueDate", "")
        url = build_url(title, notes, due)
        urls.append(url)
        if num > max_num:
            max_num = num

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")
            print(url)

    if max_num:
        write_last_processed(max_num)


if __name__ == "__main__":
    main()

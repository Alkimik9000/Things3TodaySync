#!/usr/bin/env python3
"""Process English tasks from Google Tasks and record them locally.

The script finds tasks in the ``@default`` list whose titles contain English
letters. Each task is first written to ``fetched_tasks.csv``. After confirming
the data is stored, it is deleted from Google Tasks and translated to Hebrew in
Getting Things Done (GTD) style using OpenAI. The Hebrew version is appended to
``processed_tasks.csv``. Both CSV files are stored in the repository ``outputs``
directory. Optional environment variables allow uploading the CSVs to an EC2
instance via ``scp``.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks"]
BASE_DIR = Path(__file__).resolve().parents[1]
TOKEN_FILE = str(BASE_DIR / "secrets" / "token.json")
CREDENTIALS_FILE = str(BASE_DIR / "secrets" / "credentials.json")
FETCHED_CSV = str(BASE_DIR / "outputs" / "fetched_tasks.csv")
PROCESSED_CSV = str(BASE_DIR / "outputs" / "processed_tasks.csv")


def get_service() -> Any:
    """Authorize the user and return a Google Tasks service instance."""
    creds: Any = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            assert creds is not None
            token.write(creds.to_json())

    return build("tasks", "v1", credentials=creds)


_ENG_RE = re.compile(r"[A-Za-z]")


def is_english(text: str) -> bool:
    """Return True if ``text`` contains any English letters."""
    return bool(_ENG_RE.search(text))


def rephrase_hebrew(title: str) -> str:
    """Use OpenAI API to translate ``title`` to Hebrew in GTD style."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    openai.api_key = api_key

    messages = [
        {
            "role": "system",
            "content": (
                "You translate task titles from English to Hebrew and rewrite "
                "them concisely following Getting Things Done principles. "
                "Add two relevant emojis at the end of the sentence."
            ),
        },
        {"role": "user", "content": title},
    ]
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return str(response.choices[0].message.content).strip()


def next_task_number(csv_file: str) -> int:
    """Return the next sequential task number for ``csv_file``."""
    if not os.path.exists(csv_file):
        return 1
    with open(csv_file, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f)) + 1


def append_rows(csv_file: str, rows: List[Dict[str, Optional[str]]]) -> None:
    """Append ``rows`` to ``csv_file``, writing a header if needed."""
    file_exists = os.path.exists(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["TaskNumber", "TaskTitle", "TaskNotes", "DueDate"]
        )
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def upload_to_ec2(local_path: str, remote_env: str) -> None:
    """Upload ``local_path`` to EC2 using ``scp`` if ``remote_env`` is set."""
    remote_csv = os.environ.get(remote_env)
    if not remote_csv:
        return

    ec2_user = os.environ.get("EC2_USER", "ubuntu")
    ec2_host = os.environ.get("EC2_HOST")
    ec2_key = os.environ.get("EC2_KEY_PATH")

    if not ec2_host or not ec2_key:
        raise RuntimeError("EC2_HOST and EC2_KEY_PATH must be set for upload")

    subprocess.run(
        ["scp", "-i", ec2_key, local_path, f"{ec2_user}@{ec2_host}:{remote_csv}"],
        check=True,
    )


def main() -> None:
    service = get_service()
    response = service.tasks().list(tasklist="@default").execute()
    items = response.get("items", [])

    tasks: List[Dict[str, Any]] = []
    for item in items:
        title = item.get("title", "")
        if not is_english(title):
            continue
        tasks.append(item)

    if not tasks:
        print("No English tasks found")
        return

    next_num = next_task_number(FETCHED_CSV)
    fetched_rows: List[Dict[str, Optional[str]]] = []
    processed_rows: List[Dict[str, Optional[str]]] = []

    for idx, item in enumerate(tasks, start=next_num):
        title = item.get("title", "")
        notes = item.get("notes", "")
        due = item.get("due")
        number = f"{idx:04d}"
        fetched_rows.append(
            {
                "TaskNumber": number,
                "TaskTitle": title,
                "TaskNotes": notes,
                "DueDate": due,
            }
        )
        hebrew = rephrase_hebrew(title)
        processed_rows.append(
            {
                "TaskNumber": number,
                "TaskTitle": hebrew,
                "TaskNotes": notes,
                "DueDate": due,
            }
        )

    # Write CSVs before deleting tasks
    append_rows(FETCHED_CSV, fetched_rows)
    append_rows(PROCESSED_CSV, processed_rows)

    for item in tasks:
        service.tasks().delete(tasklist="@default", task=item["id"]).execute()
        print(f"Removed task: {item.get('title', '')}")

    upload_to_ec2(FETCHED_CSV, "REMOTE_FETCHED_CSV")
    upload_to_ec2(PROCESSED_CSV, "REMOTE_PROCESSED_CSV")


if __name__ == "__main__":
    main()

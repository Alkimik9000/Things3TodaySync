#!/usr/bin/env python3
"""Detect English tasks in Google Tasks, translate them to Hebrew and store.

This script connects to Google Tasks, finds tasks whose title contains English
letters, deletes them, translates the title to Hebrew using OpenAI's API in a
style consistent with Getting Things Done, and writes the original title,
due date and the Hebrew title to ``english_tasks.csv``. The CSV is then
uploaded to an EC2 instance using ``scp`` with configuration from environment
variables.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

import openai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
CSV_FILE = "english_tasks.csv"


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
                "them concisely following Getting Things Done principles with "
                "appropriate emoji."
            ),
        },
        {"role": "user", "content": title},
    ]
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return str(response.choices[0].message.content).strip()


def upload_to_ec2(local_path: str) -> None:
    """Upload ``local_path`` to EC2 using ``scp``."""
    ec2_user = os.environ.get("EC2_USER", "ubuntu")
    ec2_host = os.environ.get("EC2_HOST")
    ec2_key = os.environ.get("EC2_KEY_PATH")
    remote_csv = os.environ.get("REMOTE_ENGLISH_CSV")

    if not ec2_host or not ec2_key or not remote_csv:
        raise RuntimeError("EC2_HOST, EC2_KEY_PATH and REMOTE_ENGLISH_CSV must be set")

    subprocess.run(
        ["scp", "-i", ec2_key, local_path, f"{ec2_user}@{ec2_host}:{remote_csv}"],
        check=True,
    )


def main() -> None:
    service = get_service()
    response = service.tasks().list(tasklist="@default").execute()
    items = response.get("items", [])

    rows: List[Dict[str, Optional[str]]] = []

    for item in items:
        title = item.get("title", "")
        if not is_english(title):
            continue
        hebrew = rephrase_hebrew(title)
        due = item.get("due")  # ISO 8601 if present
        rows.append({"english_title": title, "due": due, "hebrew_title": hebrew})
        service.tasks().delete(tasklist="@default", task=item["id"]).execute()
        print(f"Processed and removed task: {title}")

    if not rows:
        print("No English tasks found")
        return

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["english_title", "due", "hebrew_title"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} tasks to {CSV_FILE}")
    upload_to_ec2(CSV_FILE)
    print("Upload completed")


if __name__ == "__main__":
    main()

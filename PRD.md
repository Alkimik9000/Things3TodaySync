# Product Requirements Document (PRD)

## Overview
This repository provides a set of tools to sync tasks from Things3 (a task management app) to Google Tasks, enabling cross-platform access to task lists. It includes scripts for extracting tasks from Things3, syncing them to Google Tasks, and automating the process via cron jobs. Additionally, a server component supports integration with Apple Shortcuts for creating and serving Things3 links.

## Goals
- Enable users to access their Things3 tasks from Google Tasks on multiple platforms (e.g., Android, web).
- Automate the syncing process to keep tasks up-to-date with minimal user intervention.
- Provide a seamless experience for users who rely on both Things3 and Google Tasks for task management.

## Features
- **Task Extraction:**  
  - Scripts to extract "Today," "Upcoming," and "Anytime" tasks from Things3 into CSV files.
  - Output files are stored in the `outputs/` directory.
- **Task Syncing:**  
  - A script to import tasks from the generated CSV files into corresponding Google Tasks lists.
  - Deduplication logic to prevent duplicate tasks within and across lists.
- **Automation:**  
  - Shell scripts (`@sync_all_lists.sh`, `@sync_today.sh`) to automate the extraction and syncing process.
  - Cron job configurations (`@com.things3.all_lists_sync.plist`, `@com.things3.today_sync.plist`) to run the scripts periodically.
- **Server Component:**  
  - Tools for creating and serving Things3 links, supporting integration with Apple Shortcuts.
  - Includes a script (`@server/process_english_tasks.py`) for handling English-language tasks separately.

## User Stories
- As a user, I want to automatically sync my Things3 tasks to Google Tasks so that I can access them from my Android device or other platforms.
- As a user, I want to ensure that there are no duplicate tasks in my Google Tasks lists.
- As a user, I want to be able to create and manage Things3 links using Apple Shortcuts.

## Functional Requirements
- **Extraction Scripts (`@extract_tasks.py`, `@extract_upcoming.py`, `@extract_anytime.py`):**  
  - Must correctly extract tasks from Things3 based on their categories (Today, Upcoming, Anytime).
  - Must output tasks to CSV files in the `outputs/` directory.
- **Import Script (`@import_google_tasks.py`):**  
  - Must read the generated CSV files and sync tasks to the corresponding Google Tasks lists.
  - Must handle deduplication to prevent duplicate tasks within and across lists.
- **Server Component (`@server/README.md`):**  
  - Must generate and serve Things3 links correctly for use with Apple Shortcuts.
  - Must handle English tasks separately if required by the user's workflow.
- **Automation:**  
  - Shell scripts must orchestrate the extraction and syncing process in the correct order.
  - Cron jobs must be configurable to run the scripts at user-defined intervals.

## Non-Functional Requirements
- **Performance:**  
  - Scripts should be efficient and not cause significant delays during execution.
- **Error Handling:**  
  - Robust logging and error reporting to facilitate troubleshooting.
  - Logs should be stored in `outputs/things_sync.log`.
- **Setup and Configuration:**  
  - Clear instructions for setting up the environment, including dependencies and configuration files.
  - Users must be guided through configuring API credentials and other secrets.

## Constraints
- Requires Things3 to be installed and configured on the user's system.
- Requires access to the Google Tasks API, necessitating API credentials stored in the `secrets/` directory.
- The server component may require specific environment settings (e.g., Python version, installed dependencies).

## Future Enhancements
- Support for additional task lists or custom filters beyond "Today," "Upcoming," and "Anytime."
- Two-way syncing to allow changes in Google Tasks to reflect back in Things3.
- Enhanced error handling and user notifications (e.g., email alerts on sync failures).

## Workflow Summary
The following table outlines the workflow orchestrated by `@sync_all_lists.sh`:

| Order | Script Name                     | Purpose/Action                                 | Output File(s)                |
|-------|---------------------------------|------------------------------------------------|-------------------------------|
| 1     | `@extract_tasks.py`              | Extracts "Today" tasks from Things3            | `outputs/today_view.csv`      |
| 2     | `@extract_upcoming.py`           | Extracts "Upcoming" tasks from Things3         | `outputs/upcoming_tasks.csv`  |
| 3     | `@extract_anytime.py`            | Extracts "Anytime" tasks from Things3          | `outputs/anytime_tasks.csv`   |
| 4     | `@import_google_tasks.py`        | Syncs all extracted tasks to Google Tasks      | (Updates Google Tasks lists)  |

- **Logging:** Each step logs progress and errors to `outputs/things_sync.log`.
- **Error Handling:** If any extraction or sync step fails, the script exits with an error. 
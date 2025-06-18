# Product Requirements Document (PRD)

## Overview
This server directory hosts scripts that process tasks from Google Tasks and return them to Things3 through Apple Shortcuts. It runs independently from the macOS workflow and is intended for a remote Linux machine.

## Goals
- Continuously process English-titled tasks from Google Tasks and translate them to Hebrew.
- Provide a simple way to deliver the translated tasks back into Things3 using generated URL links.
- Allow fully automated operation via cron and optional upload of CSV results to a separate server.

## Features
- **English Task Processing**
  - `@process_english_tasks.py` fetches English tasks from the `@default` list.
  - Tasks are logged to `@outputs/fetched_tasks.csv` then removed from Google Tasks.
  - Titles are rephrased to Hebrew via the OpenAI API and stored in `@outputs/processed_tasks.csv`.
  - Supports uploading the CSV files to a remote host when environment variables are configured.
- **Apple Shortcuts Integration**
  - `@apple_shortcuts/create_things_links.py` converts processed tasks to Things URL links and records the last processed row.
  - `@apple_shortcuts/serve_things_links.py` exposes an HTTP endpoint that serves the next link for Apple Shortcuts.
  - `@apple_shortcuts/setup_link_server.sh` installs a systemd service so the server starts automatically.
- **Automation**
  - `@run_processor.sh` loads environment variables from `.env` and runs `@process_english_tasks.py`, making it easy to schedule with cron.
  - Example environment variables are provided in `@env.example`.

## User Stories
- As a user, I want English tasks in Google Tasks to be automatically translated and archived.
- As a user, I want to fetch new Things links over HTTP so I can run them with Apple Shortcuts.
- As a user, I want to schedule the processor on my server without manual intervention.

## Functional Requirements
- **`@process_english_tasks.py`**
  - Must detect tasks containing English text.
  - Must append task details to `@fetched_tasks.csv` before deletion.
  - Must translate each title using the OpenAI API and write results to `@processed_tasks.csv`.
  - Must respect optional environment variables for uploading the CSVs to a remote host.
- **`@apple_shortcuts/create_things_links.py`**
  - Must only process rows whose `TaskNumber` is greater than the stored state.
  - Must generate Things links that include title, notes and due date.
  - Must append the links to `@generated_things_urls.txt`.
- **`@apple_shortcuts/serve_things_links.py`**
  - Must serve the next unserved link at `/next`.
  - Must store the last served index so each link is delivered once.
- **Automation Scripts**
  - `@run_processor.sh` must load environment variables and write logs to `@english_tasks.log`.
  - `@apple_shortcuts/setup_link_server.sh` must create a `things-links` systemd service.

## Non-Functional Requirements
- **Performance**: Scripts should complete quickly and avoid long-running network operations.
- **Reliability**: Errors should be logged to `@english_tasks.log` to aid troubleshooting.
- **Security**: API credentials (`@credentials.json` and `@token.json`) must remain outside the repository and only example files are committed.

## Constraints
- Requires Python 3 and the packages listed in `@server/README.md`.
- Requires valid Google and OpenAI credentials and a `.env` file with configuration variables.
- If uploading results, SSH access to the target server must be configured.

## Future Enhancements
- Support additional language detection beyond simple English letters.
- Web interface for monitoring queued links and processed tasks.
- Automated cleanup of old CSV files.

## Workflow Summary
The typical server workflow consists of the following steps:

| Order | Script Name                                 | Purpose/Action                                    | Output File(s)                       |
|-------|---------------------------------------------|---------------------------------------------------|--------------------------------------|
| 1     | `@process_english_tasks.py`                  | Fetch English tasks, translate and store results  | `@outputs/fetched_tasks.csv`, `@outputs/processed_tasks.csv` |
| 2     | `@apple_shortcuts/create_things_links.py`    | Generate Things URLs from processed tasks         | `@apple_shortcuts/generated_things_urls.txt` |
| 3     | `@apple_shortcuts/serve_things_links.py`     | Provide the next URL over HTTP for Apple Shortcuts| (serves links from file)             |
| 4     | `@run_processor.sh` (via cron)               | Periodically run the processor and log output     | `@english_tasks.log`                  |

- **Logging:** The processor and link server record activity in `@english_tasks.log` or standard output.
- **Error Handling:** Failures in any step should produce an error message in the log and exit with a non-zero status. 
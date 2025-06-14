# Server Components

This directory contains scripts intended to run on the remote EC2 instance.

## `process_english_tasks.py`

Detects tasks with English titles from your Google Tasks `@default` list. Each
task's details are appended to `fetched_tasks.csv` and then removed from Google
Tasks. The title is translated to Hebrew in GTD style with a short phrase and
two emojis using the OpenAI API. The result is saved in `processed_tasks.csv`.
Both CSVs are written under `server/outputs` and can optionally be uploaded to
an EC2 server.

### Requirements
Install the following dependencies on the EC2 instance:

- `python3` and `python3-pip` (install with `sudo apt install python3 python3-pip`)
- Python packages: `google-api-python-client`, `google-auth-oauthlib`, `openai`, `pandas`
  (install with `pip3 install --user google-api-python-client google-auth-oauthlib openai pandas`)
- `scp` command from the `openssh-client` package
- OAuth credentials (`credentials.json`) and token (`token.json`) placed in this directory. Example files `credentials.json.example` and `token.json.example` are provided.
- Environment variables configured in a `.env` file. Start by copying `env.example` to `.env` and update the values. Optional variables `REMOTE_FETCHED_CSV` and `REMOTE_PROCESSED_CSV` can be set if you want the CSVs uploaded via `scp`.

### Running

```bash
cd server
python3 process_english_tasks.py
```

To keep processing tasks automatically on the server, schedule the wrapper
script using `cron`. It loads environment variables from `.env` and writes a
log file `english_tasks.log`:

```bash
*/10 * * * * /path/to/repo/server/run_processor.sh
```

This example runs every ten minutes.

## iPad link scripts

The `ipad_links` folder contains tools for delivering processed tasks to Things
on your iPad.

### `create_things_links.py`

Generate Things URL links from the tasks stored in `processed_tasks.csv`. The
script keeps track of the last processed row using `last_linked_task.txt` and
appends new links to `generated_things_urls.txt`. Each link includes the task's
title, notes and due date (if present) and schedules it for the **Today** list.

Run it from within the `ipad_links` directory:

```bash
cd ipad_links
python3 create_things_links.py
```

### `serve_things_links.py`

Serve the generated Things links over HTTP so a Shortcuts automation on your
iPad can fetch them. Start it from the same directory:

```bash
cd ipad_links
python3 serve_things_links.py
```

The next unserved link is available at `http://<server-ip>:8000/next`.

#### Auto-start on Ubuntu

Use the provided helper script to install a `systemd` service that runs the
server automatically:

```bash
sudo ./ipad_links/setup_link_server.sh
```

This creates and starts a service named `things-links` so the HTTP server
launches on boot.

For a reference of the Things URL scheme used by these scripts, see
[`ipad_links/things_url_scheme.md`](ipad_links/things_url_scheme.md).


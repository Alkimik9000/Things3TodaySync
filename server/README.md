# Server Components

This directory contains scripts intended to run on the remote EC2 instance.

## `process_english_tasks.py`

Detects tasks with English titles from your Google Tasks `@default` list. Each
task's details are appended to `fetched_tasks.csv` and then removed from Google
Tasks. The title is translated to Hebrew in GTD style with a short phrase and
two emojis using the OpenAI API. The result is saved in `processed_tasks.csv`.
Both CSVs reside in this directory and can optionally be uploaded to an EC2
server.

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


# Server Components

This directory contains scripts intended to run on the remote EC2 instance.

## `process_english_tasks.py`

Detects tasks written in English from your Google Tasks list, translates them
into Hebrew using the OpenAI API and stores the original and translated titles
in `english_tasks.csv`. The CSV is uploaded to the EC2 server after processing.

### Requirements
- Python 3 with `google-api-python-client`, `google-auth-oauthlib` and
  `openai` installed
- OAuth credentials (`credentials.json`) and token (`token.json`) placed in this
  directory
- Environment variables as shown in `env.example`

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


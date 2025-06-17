# Generating Things URLs from Processed Tasks

`server/apple_shortcuts/create_things_links.py` converts rows in `processed_tasks.csv` into URLs that use the `things:///add` scheme. Each URL opens Things and pre‑populates a new task in the **Today** list. These links can be used by Apple Shortcuts on macOS, iPadOS or iOS.

## How it works

1. **Track previously processed rows**
   - The script stores the highest `TaskNumber` it has handled in `last_linked_task.txt`.
   - Only rows with a larger `TaskNumber` are processed on the next run.
2. **Generate URLs**
   - For each new row, the task title, notes, and due date are encoded into the URL parameters.
   - The task is scheduled for *Today* using `when=today` so it bypasses the Inbox.
   - URLs are appended to `generated_things_urls.txt` and also printed to stdout.

## Usage

Run the script from the repository root:

```bash
python3 server/apple_shortcuts/create_things_links.py
```

If there are new rows, the script outputs URLs similar to:

```
things:///add?title=Buy%20milk&notes=Check%20expiration&deadline=2025-06-16&when=today
```

## Serving the URLs

Start a tiny HTTP server so an Apple Shortcut can fetch the links:

```bash
python3 server/apple_shortcuts/serve_things_links.py
```

The server exposes `/next`, returning the next unserved link from
`generated_things_urls.txt`. Set the `PORT` environment variable to change the
port if needed.

### Running on Ubuntu EC2

Run the helper script to install a `systemd` service so the server starts
automatically at boot:

```bash
sudo ./server/apple_shortcuts/setup_link_server.sh
```

The service is named `things-links` and listens on port `8000` by default.

## Apple Shortcuts automation

Create an Apple Shortcut named **Fetch Things Link** that:

1. **Get Contents of URL** – `http://<server-ip>:8000/next`
2. **If** the result is not empty, **Open URLs** with the result

Schedule this shortcut to run at your preferred interval so new tasks appear in
Things automatically.

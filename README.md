# Things3 ↔ Google Tasks Sync

**A cross-platform bridge for your tasks.** This project began as a simple script to export the
Things3 *Today* view. It has evolved into a two‑way workflow that keeps
Things3 in sync with Google Tasks, enabling access to your to‑dos on any
device.

## Why?

Things3 works beautifully on macOS and iOS but it is locked to the Apple
ec osystem. I needed my task list on Android and other platforms, so this
project was born. The scripts here extract tasks from Things3 using
AppleScript and Python, synchronise them with Google Tasks and optionally
process tasks from Google Tasks back into Things3.

## Key Features

- **Two‑way synchronisation** – export from Things3 and import from Google Tasks.
- **Task extraction** – grab tasks from the *Today*, *Upcoming* and
  *Anytime* lists as CSV files.
- **Time support** – Today exports now include a `DueTime` column with the
  task's time in 24‑hour format when available.
- **Google Tasks integration** – `import_google_tasks.py` keeps your
  Google list aligned with the CSV data.
- **Server processing** – optional scripts under `server/` pull English
  tasks from Google, translate them to Hebrew via OpenAI and prepare
  Things links for easy re‑entry via Apple Shortcuts.
- **Launch agent / cron** – run the sync automatically every ten minutes
  with `sync_today.sh` and `com.things3.today_sync.plist`.
- **Detailed logs** – monitor operations and keep the last 24 hours of
  output.

## Prerequisites

- **macOS** with Things3 installed
- **Python 3.x** (included with macOS)
- Google account for Google Tasks

Optional server features require Python 3 on Linux and the
packages noted in [`server/README.md`](server/README.md).

## Setup

1. Clone this repository

   ```bash
   git clone https://github.com/yourusername/Things3TodaySync.git
   cd Things3TodaySync
   ```

2. Install dependencies

   ```bash
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 pandas openai
   ```

3. Copy the example configuration and edit as needed

   ```bash
   cp config.sh.example config.sh
   nano config.sh
   ```

4. Place Google OAuth credentials in `secrets/credentials.json` and run
   the sync once to create `secrets/token.json`

   ```bash
   ./sync_today.sh
   ```

   A browser window will prompt for Google authorisation.

5. (Optional) Install the launch agent to run every 10 minutes

   ```bash
   cp com.things3.today_sync.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.things3.today_sync.plist
   ```

## Usage

Run the sync manually at any time:

```bash
./sync_today.sh
```

CSV exports will appear in the `outputs/` directory. The Google Tasks list
is updated accordingly. Check `sync.log` for detailed output.

For server‑side processing or Apple Shortcut link generation, see the
[server README](server/README.md).

## Repository Status

The name *Things3TodaySync* reflects the original single‑direction export.
The project now supports two‑way synchronisation with Google Tasks and may
be renamed in future to better reflect its scope.

## License

This project is licensed under the MIT License. See
[LICENSE](LICENSE) for details.

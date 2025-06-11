# Things3 Today View Sync

A lightweight utility to sync your Things3 Today view with a remote server.

## Features

- Automatic extraction of Today's tasks from Things3
- Secure sync to a remote server every minute
- Detailed logging for monitoring
- macOS launch agent for continuous operation
- Minimal resource usage

## Prerequisites

- **macOS** with Things3 installed
- **Python 3.x** (included with macOS)
- `rsync` command-line tool (included with macOS)

## Local macOS Setup

### Automated Setup (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Things3-Android-Companion-App-Detailed.git
   cd Things3-Android-Companion-App-Detailed
   ```

2. Run the setup script and follow the prompts:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

### Manual Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Things3-Android-Companion-App-Detailed.git
   cd Things3-Android-Companion-App-Detailed
   ```

2. Copy the example configuration and update it:
   ```bash
   cp config.sh.example config.sh
   chmod +x config.sh
   nano config.sh  # Edit with your EC2 server details
   ```

3. Make the scripts executable:
   ```bash
   chmod +x setup.sh sync_things.sh
   ```

4. Run the setup script:
   ```bash
   ./setup.sh
   ```
   This will:
   - Create necessary directories
   - Set up the launch agent
   - Start the sync service

5. The script will run in the background and automatically start on login.

6. The Today view will be synced every minute to the specified remote location.

## Automatic Startup (Launch Agent)

To run the sync automatically in the background:

```bash
# Copy the launch agent to your user's LaunchAgents directory
cp com.things3.sync.plist ~/Library/LaunchAgents/

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.things3.sync.plist
```

The agent will automatically start the sync script when you log in and keep it running.

To stop the automatic sync:
```bash
launchctl unload ~/Library/LaunchAgents/com.things3.sync.plist
```

## Configuration

1. Copy `config.sh.example` to `config.sh` and update the following variables:
   - `EC2_HOST`: Your server's IP or hostname
   - `EC2_KEY_PATH`: Path to your SSH private key
   - `EC2_USER`: SSH username (default: `ubuntu`)
   - `REMOTE_DIR`: Base directory on the remote server
   - `REMOTE_CSV`: Full path where the CSV should be stored (default: `$REMOTE_DIR/today_view.csv`)

## Usage

### Manual Sync

Run a single sync operation:
```bash
./sync_things.sh
```

### Logs and Monitoring

- View the sync logs:
  ```bash
  tail -f things_sync.log
  ```

- Check the service status:
  ```bash
  launchctl list | grep things3
  ```

- View the latest Today view CSV locally:
  ```bash
  cat today_view.csv
  ```

- View the latest synced file on the remote server:
  ```bash
  ssh -i /path/to/your/key $EC2_USER@$EC2_HOST "cat $REMOTE_CSV"
  ```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure your SSH key has the correct permissions: `chmod 600 ~/.ssh/your-key.pem`
   - Verify the EC2 user has write access to the remote directory

2. **Sync Not Starting**
   - Check the launch agent status: `launchctl list | grep things3`
   - View launch agent logs in Console.app (search for "sync_things")


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

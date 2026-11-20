# File & Folder Watcher

Local Python utility for monitoring directory changes (new, modified, deleted files), logging events to a file, filtering by extensions, and printing session statistics.

## Configuration

Edit `config.json` to configure:
- `target_dir` — folder to watch
- `interval_seconds` — polling interval in seconds
- `log_file` — path to log file
- `extensions` — list of extensions to watch (leave `[]` to watch all files)

## Usage

```cmd
python watcher.py

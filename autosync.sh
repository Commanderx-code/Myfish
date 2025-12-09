#!/usr/bin/env bash

# -----------------------------
# MyFish Automatic Git Sync
# -----------------------------

REPO_DIR="$HOME/MyFish"
LOG_FILE="$HOME/MyFish/autosync.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

cd "$REPO_DIR" || exit 1

# Pull first to avoid conflicts
git pull --quiet --rebase >> "$LOG_FILE" 2>&1

# Check if there are any changes
if [ -z "$(git status --porcelain)" ]; then
    echo "$TIMESTAMP | No changes detected. Skipping commit." >> "$LOG_FILE"
    exit 0
fi

# Stage all changes
git add .

# Commit with timestamp
git commit -m "Auto-sync $TIMESTAMP" >> "$LOG_FILE" 2>&1

# Push changes
git push >> "$LOG_FILE" 2>&1

# Log success
echo "$TIMESTAMP | Sync completed successfully." >> "$LOG_FILE"

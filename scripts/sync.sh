#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"
cd "$REPO"

echo "[+] Running backup..."
"$REPO/scripts/backup.sh"

echo "[+] Git sync..."
git add .
git commit -m "Manual sync $(date '+%Y-%m-%d %H:%M:%S')" || echo "[i] Nothing to commit"
git push || echo "[!] Git push failed, check network/SSH."

echo "[✓] Sync complete."

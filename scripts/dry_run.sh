#!/usr/bin/env bash
set -e

ARCHIVE="$1"
[ -z "$ARCHIVE" ] && echo "Usage: dry_run.sh backup.tar.gz" && exit 1

echo "Dry-run preview:"
tar -tzf "$ARCHIVE"


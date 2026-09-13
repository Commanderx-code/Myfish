#!/usr/bin/env bash
set -euo pipefail
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3 using your distribution package manager, then run this script again.' >&2
  exit 1
fi
exec python3 "$(dirname -- "${BASH_SOURCE[0]}")/scripts/bootstrap.py" "$@"

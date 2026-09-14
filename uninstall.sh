#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $(uname -s) == Darwin ]]; then
  # shellcheck disable=SC1091
  source "$project_dir/scripts/prerequisites.sh"
  load_homebrew || true
fi
command -v python3 >/dev/null || { echo 'Python 3 is required to run Commander-os maintenance.' >&2; exit 1; }
exec python3 "$project_dir/scripts/lifecycle.py" "$@"

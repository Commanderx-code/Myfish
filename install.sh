#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
source "$project_dir/scripts/prerequisites.sh"
init_only=false
install_missing=true
args=()
for arg in "$@"; do
  case "$arg" in
    --help|-h)
      echo 'Usage: ./install.sh [--apply] [--init] [--config PATH] [--no-install]'
      echo 'Offers to install missing prerequisites and Nix, then builds a preview.'
      echo '--apply       Ask to activate after building.'
      echo '--init        Create machine settings only (Python may be installed).'
      echo '--no-install  Do not install prerequisites or Nix.'
      exit 0 ;;
    --init) init_only=true; args+=("$arg") ;;
    --no-install) install_missing=false ;;
    *) args+=("$arg") ;;
  esac
done
[[ $(uname -s) == Linux ]] || { echo 'Only Linux is supported.' >&2; exit 1; }
((EUID != 0)) || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }
if "$install_missing"; then
  if "$init_only"; then
    ensure_packages python3
  else
    ensure_packages python3 git curl xz
    ensure_nix
  fi
fi
command -v python3 >/dev/null || { echo 'Python 3 is missing.' >&2; exit 1; }
exec python3 "$project_dir/scripts/bootstrap.py" "${args[@]}"

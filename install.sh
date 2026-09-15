#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
source "$project_dir/scripts/prerequisites.sh"
init_only=false
install_missing=true
backend=''
shell_choice=''
greeting_choice=false
args=()
while (($#)); do
  case "$1" in
    --help|-h)
      echo 'Usage: ./install.sh [--apply] [--init] [--backend home-manager|native]'
      echo '                    [--shell bash|fish|zsh|keep] [--config PATH] [--no-install]'
      echo '                    [--greeting TEXT | --no-greeting | --default-greeting]'
      echo 'Interactive setup asks for installation mode and shell before installing anything.'
      echo 'Without --apply, native mode shows a plan; Home Manager mode builds a preview.'
      exit 0 ;;
    --greeting)
      (($# >= 2)) || { echo 'Missing greeting text.' >&2; exit 1; }
      args+=("$1" "$2"); greeting_choice=true; shift 2 ;;
    --no-greeting|--default-greeting) args+=("$1"); greeting_choice=true; shift ;;
    --init) init_only=true; args+=("$1"); shift ;;
    --apply) args+=("$1"); shift ;;
    --no-install) install_missing=false; shift ;;
    --backend|--shell|--config)
      (($# >= 2)) || { echo "Missing value for $1" >&2; exit 1; }
      case "$1" in
        --backend) backend=$2 ;;
        --shell) shell_choice=$2 ;;
        --config) args+=("$1" "$2") ;;
      esac
      shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
case $(uname -s) in Linux|Darwin) ;; *) echo 'Linux and macOS are supported.' >&2; exit 1 ;; esac
((EUID != 0)) || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }
if [[ -z "$backend" ]]; then
  if [[ -t 0 ]]; then
    echo 'How should Myfish manage your setup?'
    echo '  1) Home Manager — install Nix if needed; pinned packages and generations'
    echo '  2) Direct install — distro packages and backed-up configuration files'
    read -r -p 'Choose [1/2, default 1]: ' answer
    case "$answer" in ''|1) backend=home-manager ;; 2) backend=native ;; *) exit 1 ;; esac
  else
    echo 'Specify --backend home-manager or --backend native when not running interactively.' >&2
    exit 1
  fi
fi
case "$backend" in home-manager|native) ;; *) echo 'Invalid backend.' >&2; exit 1 ;; esac
if [[ -z "$shell_choice" && -t 0 ]]; then
  echo 'Shell: 1) Fish  2) Bash  3) Zsh  4) Keep current shell  5) Reuse saved choice'
  read -r -p 'Choose [1-5, default 5]: ' answer
  case "$answer" in 1) shell_choice=fish ;; 2) shell_choice=bash ;; 3) shell_choice=zsh ;; 4) shell_choice=keep ;; ''|5) ;; *) exit 1 ;; esac
fi
if [[ -n "$shell_choice" ]]; then
  case "$shell_choice" in bash|fish|zsh|keep) args+=(--shell "$shell_choice") ;; *) echo 'Invalid shell.' >&2; exit 1 ;; esac
fi
if ! "$greeting_choice" && [[ -t 0 && "$shell_choice" != keep ]]; then
  echo 'Greeting: 1) Keep saved/default  2) Custom message  3) No greeting  4) Restore default'
  read -r -p 'Choose [1-4, default 1]: ' answer
  case "$answer" in
    ''|1) ;;
    2) read -r -p 'Greeting text ({user} inserts your username): ' greeting_text; args+=(--greeting "$greeting_text") ;;
    3) args+=(--no-greeting) ;;
    4) args+=(--default-greeting) ;;
    *) echo 'Invalid greeting choice.' >&2; exit 1 ;;
  esac
fi
if [[ $(uname -s) == Darwin ]]; then
  if "$install_missing"; then
    ensure_homebrew
  else
    load_homebrew || { echo 'Homebrew is missing and --no-install was specified.' >&2; exit 1; }
  fi
fi
if "$install_missing"; then
  ensure_packages python3
  if [[ "$backend" == home-manager ]] && ! "$init_only"; then
    ensure_packages git curl xz
    ensure_nix
  fi
fi
command -v python3 >/dev/null || { echo 'Python 3 is missing.' >&2; exit 1; }
args+=(--backend "$backend")
if [[ "$backend" == native ]]; then
  "$install_missing" || args+=(--no-install)
fi
exec python3 "$project_dir/scripts/bootstrap.py" "${args[@]}"

#!/usr/bin/env bash
# Sourced by install.sh; no actions occur merely by sourcing this file.
confirm_install() {
  local answer
  read -r -p "$1 [y/N] " answer
  [[ "$answer" == y || "$answer" == Y || "$answer" == yes ]]
}

# Homebrew bootstrap is intentionally macOS-only, including when brew exists on Linux.
load_homebrew() {
  [[ $(uname -s) == Darwin ]] || return 1
  local brew_path candidate
  brew_path=$(command -v brew || true)
  if [[ -z "$brew_path" ]]; then
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [[ -x "$candidate" ]]; then brew_path=$candidate; break; fi
    done
  fi
  [[ -n "$brew_path" ]] || return 1
  local environment
  environment=$("$brew_path" shellenv) || return
  eval "$environment"
  command -v brew >/dev/null
}

ensure_homebrew() {
  [[ $(uname -s) == Darwin ]] || return 0
  load_homebrew && return 0
  echo 'Homebrew is missing. Its official installer may request Xcode Command Line Tools and administrator access.'
  confirm_install 'Download and run the official Homebrew installer?' || return 1
  local installer result=0
  installer=$(mktemp)
  curl --fail --show-error --silent --location --proto '=https' --proto-redir '=https' --tlsv1.2 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer" || result=$?
  if ((result == 0)); then /bin/bash "$installer" || result=$?; fi
  rm -f -- "$installer"
  ((result == 0)) || return "$result"
  load_homebrew || { echo 'Homebrew setup is incomplete. Finish its reported steps, then rerun this installer.' >&2; return 1; }
}

install_packages() {
  local manager=$1
  shift
  if [[ "$manager" == brew ]]; then
    printf 'Missing Homebrew prerequisites:'
    printf ' %s' "$@"
    printf '\n'
    confirm_install 'Install these with Homebrew?' || return 1
    brew install --formula "$@"
    return
  fi
  command -v sudo >/dev/null || { echo 'sudo is required to install missing prerequisites.' >&2; return 1; }
  printf 'Missing packages:'
  printf ' %s' "$@"
  printf '\n'
  confirm_install 'Install these packages using sudo?' || return 1
  case "$manager" in
    apt-get) sudo apt-get update && sudo apt-get install -y "$@" ;;
    dnf) sudo dnf install -y "$@" ;;
    pacman) sudo pacman -S --needed --noconfirm "$@" ;;
    *) echo 'Unsupported package manager.' >&2; return 1 ;;
  esac
}

ensure_packages() {
  local tool manager='' missing=()
  if [[ $(uname -s) == Darwin ]]; then
    for tool in "$@"; do
      if [[ "$tool" == python3 ]]; then
        brew list --formula --versions python >/dev/null 2>&1 || missing+=(python)
      else
        command -v "$tool" >/dev/null || missing+=("$tool")
      fi
    done
    if [[ -n "${missing[*]-}" ]]; then install_packages brew "${missing[@]}"; fi
    return
  fi
  for tool in "$@"; do
    command -v "$tool" >/dev/null || missing+=("$tool")
  done
  [[ -n "${missing[*]-}" ]] || return 0
  for tool in apt-get dnf pacman; do
    if command -v "$tool" >/dev/null; then manager=$tool; break; fi
  done
  if [[ -z "$manager" ]]; then
    echo "Install these tools with your distribution package manager: ${missing[*]}" >&2
    return 1
  fi
  # Arch names its Python 3 package python.
  if [[ "$manager" == pacman ]]; then
    for tool in "${!missing[@]}"; do
      [[ "${missing[$tool]}" != python3 ]] || missing[tool]=python
    done
  fi
  for tool in "${!missing[@]}"; do
    if [[ "${missing[$tool]}" == xz && "$manager" == apt-get ]]; then
      missing[tool]=xz-utils
    fi
  done
  install_packages "$manager" "${missing[@]}"
}

load_nix() {
  if [[ -r /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]]; then
    # shellcheck disable=SC1091
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
  elif [[ -r "$HOME/.nix-profile/etc/profile.d/nix.sh" ]]; then
    # shellcheck disable=SC1091
    . "$HOME/.nix-profile/etc/profile.d/nix.sh"
  fi
}

ensure_nix() {
  command -v nix >/dev/null && return 0
  load_nix
  command -v nix >/dev/null && return 0
  if [[ $(uname -s) != Darwin && ! -d /run/systemd/system ]]; then
    echo 'Automatic Nix installation currently requires systemd. See https://nixos.org/download/.' >&2
    return 1
  fi
  if [[ -e /sys/fs/selinux/enforce ]] || { command -v selinuxenabled >/dev/null && selinuxenabled; }; then
    echo 'SELinux is enabled. Automatic Nix installation is unavailable; see https://nixos.org/download/.' >&2
    return 1
  fi
  if [[ -d /nix ]]; then
    echo 'An existing /nix installation was found but nix is unavailable. Repair it before continuing.' >&2
    return 1
  fi
  command -v sudo >/dev/null || { echo 'sudo is required for the multi-user Nix installation.' >&2; return 1; }
  echo 'Nix will install into /nix and create build users and a system daemon.'
  if [[ $(uname -s) == Darwin ]]; then
    echo 'On macOS the official installer may create an APFS volume and launchd service.'
  fi
  confirm_install 'Download and run the official Nix installer?' || return 1
  local installer result=0
  installer=$(mktemp)
  curl --fail --show-error --silent --location --proto '=https' --proto-redir '=https' --tlsv1.2 \
    https://nixos.org/nix/install -o "$installer" || result=$?
  if ((result == 0)); then
    sh "$installer" --daemon || result=$?
  fi
  rm -f -- "$installer"
  ((result == 0)) || return "$result"
  load_nix
  command -v nix >/dev/null || { echo 'Open a new terminal and rerun the installer to load Nix.' >&2; return 1; }
}

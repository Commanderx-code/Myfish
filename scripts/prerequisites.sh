#!/usr/bin/env bash
# Sourced by install.sh; no actions occur merely by sourcing this file.
confirm_install() {
  local answer
  read -r -p "$1 [y/N] " answer
  [[ "$answer" == y || "$answer" == Y || "$answer" == yes ]]
}

install_packages() {
  local manager=$1
  shift
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
  for tool in "$@"; do
    command -v "$tool" >/dev/null || missing+=("$tool")
  done
  ((${#missing[@]})) || return 0
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
  if [[ ! -d /run/systemd/system ]]; then
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
  echo 'Nix will install into /nix and create build users and a system service.'
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

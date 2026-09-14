# shellcheck shell=bash
# Native macOS startup: keep Homebrew and GNU helper tools available after login.
[ "$(uname -s)" = Darwin ] || return
_commander_brew=${HOMEBREW_PREFIX:-}
if [ -z "$_commander_brew" ]; then
  if [ -x /opt/homebrew/bin/brew ]; then _commander_brew=/opt/homebrew
  elif [ -x /usr/local/bin/brew ]; then _commander_brew=/usr/local
  fi
fi
if [ -n "$_commander_brew" ]; then
  export HOMEBREW_PREFIX="$_commander_brew"
  for _commander_path in "$_commander_brew/bin" "$_commander_brew/sbin" \
    "$_commander_brew/opt/coreutils/libexec/gnubin" "$_commander_brew/opt/gnu-tar/libexec/gnubin" \
    "$_commander_brew/opt/trash-cli/bin"; do
    case ":$PATH:" in *":$_commander_path:"*) ;; *) export PATH="$_commander_path:$PATH" ;; esac
  done
fi
unset _commander_brew _commander_path

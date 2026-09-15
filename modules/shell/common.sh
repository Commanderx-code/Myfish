# shellcheck shell=bash
# Shared interactive helpers for Bash and Zsh. Source after shell integrations.
case $- in *i*) ;; *) return ;; esac

_commander_editor() {
  local editor
  for editor in nvim vim nano vi; do
    if command -v "$editor" >/dev/null 2>&1; then printf '%s\n' "$editor"; return; fi
  done
  echo 'No supported editor found.' >&2
  return 1
}
_commander_fd() {
  if command -v fd >/dev/null 2>&1; then command fd "$@"; else command fdfind "$@"; fi
}
mkcd() {
  [ "$#" -eq 1 ] || { echo 'Usage: mkcd <directory>' >&2; return 1; }
  command mkdir -p -- "$1" && cd -- "$1" || return
}
dirsize() { du -sh .; }
psg() {
  [ "$#" -ge 1 ] || { echo 'Usage: psg <pattern>' >&2; return 1; }
  if [ "$(uname -s)" = Darwin ]; then pgrep -ifl -- "$1"; else pgrep -ai -- "$1"; fi
}
serve() { python3 -m http.server --bind 127.0.0.1 "${1:-8000}"; }
gcom() {
  [ "$#" -gt 0 ] || { echo 'Usage: gcom <message>' >&2; return 1; }
  git add . && git commit -m "$*"
}
lazyg() { gcom "$@" && git push; }
fcd() {
  local selected
  IFS= read -r -d '' selected < <(_commander_fd --type d --hidden --exclude .git --print0 | fzf --read0 --print0) || return 0
  cd -- "$selected" || return
}
fdi() {
  local selected preview editor
  printf -v preview 'bash %q {}' "$HOME/.local/bin/fzf-preview"
  IFS= read -r -d '' selected < <(_commander_fd --type f --hidden --exclude .git --exclude node_modules --print0 |
    fzf --read0 --print0 --preview "$preview" --preview-window 'right,60%,nowrap') || return 0
  editor=$(_commander_editor) || return
  "$editor" "$selected"
}
rgi() {
  local query selected filename line editor
  if [ "$#" -gt 0 ]; then query=$*; else
    printf 'Search text: '
    IFS= read -r query || return
  fi
  [ -n "$query" ] || return 0
  selected=$(rg --line-number --no-heading --color=always --smart-case --hidden --glob '!.git/*' -- "$query" . |
    fzf --ansi --delimiter ':' --preview 'bat --style=numbers --color=always --highlight-line {2} {1}' --preview-window 'right,60%,nowrap') || return 0
  filename=${selected%%:*}
  selected=${selected#*:}
  line=${selected%%:*}
  editor=$(_commander_editor) || return
  "$editor" "+$line" "$filename"
}
extract() {
  [ "$#" -eq 1 ] && [ -f "$1" ] || { echo 'Usage: extract <archive-file>' >&2; return 1; }
  local archive
  archive=$(realpath -- "$1") || return
  case "$archive" in
    *.tar|*.tar.gz|*.tgz|*.tar.bz2|*.tbz2|*.tar.xz|*.txz|*.tar.zst) command tar -xf "$archive" ;;
    *.zip) command unzip "$archive" ;;
    *.gz) command gunzip -- "$archive" ;;
    *.bz2) command bunzip2 -- "$archive" ;;
    *.xz) command unxz -- "$archive" ;;
    *.7z|*.rar) if command -v 7z >/dev/null 2>&1; then command 7z x "$archive"; else command 7zz x "$archive"; fi ;;
    *) echo "Unsupported archive: $archive" >&2; return 1 ;;
  esac
}
br() {
  command -v broot >/dev/null 2>&1 || { echo 'Install broot to use br.' >&2; return 1; }
  local output result
  output=$(mktemp) || return
  command broot --outcmd "$output" "$@"
  result=$?
  # shellcheck disable=SC1090
  if [ "$result" -eq 0 ]; then . "$output"; result=$?; fi
  command rm -f -- "$output"
  return "$result"
}
# Explicit notification wrapper avoids replacing existing Bash/Zsh prompt hooks.
notify-run() {
  [ "$#" -gt 0 ] || { echo 'Usage: notify-run <command> [arguments]' >&2; return 1; }
  local result
  "$@"; result=$?
  if [ "$(uname -s)" = Darwin ] && command -v osascript >/dev/null 2>&1; then
    osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Commander-os"' -e 'end run' "Exit status: $result" >/dev/null 2>&1 || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send --app-name=Commander-os 'Command finished' "Exit status: $result" || true
  fi
  return "$result"
}

export BAT_PAGER=''
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac
if command -v nvim >/dev/null 2>&1; then
  export EDITOR="${EDITOR:-nvim}" VISUAL="${VISUAL:-nvim}"
  alias vim=nvim
fi
if ! command -v bat >/dev/null 2>&1 && command -v batcat >/dev/null 2>&1; then alias bat=batcat; fi
if ! command -v fd >/dev/null 2>&1 && command -v fdfind >/dev/null 2>&1; then alias fd=fdfind; fi
alias cp='cp -i' mv='mv -i'
if command -v trash >/dev/null 2>&1; then alias rm='trash -v'; fi
alias cat=bat ccat='command cat' grep=rg cgrep='command grep' find=fd cfind='command find'
alias cls=clear
if [ "$(uname -s)" = Darwin ]; then
  alias psa='ps aux' mountedinfo='df -h'
else
  alias psa='ps auxf' mountedinfo='df -hT'
fi
alias da='date "+%Y-%m-%d %A %T %Z"'
alias gs='git status' ga='git add' gc='git commit' gp='git push' gl='git pull'
if command -v lazygit >/dev/null 2>&1; then alias lg=lazygit; fi
alias ..='cd ..' ...='cd ../..' ....='cd ../../..' .....='cd ../../../..' bd='cd -' home='cd ~'
alias cdi=fcd fzf_open_file=fdi fzf_rg_search=rgi
export EZA_COLORS='da=1;34:di=1;36:fi=0;37:ex=1;32:*.zip=1;31:*.tar=1;31:*.gz=1;31:*.jpg=1;35:*.png=1;35'
alias ls='eza --icons --group-directories-first --colour=always'
alias ll='eza -lh --icons --group-directories-first --time-style=long-iso'
alias la='eza -lha --icons --group-directories-first' tree='eza --tree --level=2 --icons'
alias lx='eza -lh --sort=extension --icons' lk='eza -lh --sort=size --icons' lt='eza -lh --sort=modified --icons'
alias ldir='eza -l --icons --only-dirs' lf='eza -l --icons --only-files'
alias lgit='eza -l --git --icons' l1='eza -1 --icons' lr='eza -R --icons'
_commander_finder=fd
command -v fd >/dev/null 2>&1 || _commander_finder=fdfind
export FZF_DEFAULT_COMMAND="$_commander_finder --type f --hidden --exclude .git --exclude node_modules --exclude .cache"
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND="$_commander_finder --type d --hidden --exclude .git --exclude node_modules --exclude .cache"
export FZF_DEFAULT_OPTS='--layout=reverse --border --ansi --preview-window=right,60%,nowrap --bind=ctrl-/:toggle-preview'
unset _commander_finder
if [ -z "${COMMANDER_QUIET+x}" ]; then
  _commander_greeting_file="${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/greeting.txt"
  if [ -f "$_commander_greeting_file" ]; then
    _commander_greeting=$(command cat -- "$_commander_greeting_file")
    [ -z "$_commander_greeting" ] || printf '%s\n' "$_commander_greeting"
  else
    printf 'Hello, %s ⚡\n' "$(whoami)"
  fi
  unset _commander_greeting_file _commander_greeting
  if command -v fastfetch >/dev/null 2>&1; then fastfetch; fi
fi

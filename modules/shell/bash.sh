# shellcheck shell=bash
# Bash Readline bindings. Load after fzf and the shared helpers.
case $- in *i*) ;; *) return ;; esac
bind -x '"\C-p":fdi'
bind -x '"\C-f":rgi'
# Preserve the native Ctrl-R history shortcut; **Tab uses fzf completion.
bind 'set colored-stats on'
bind 'set completion-ignore-case on'

if declare -F __fzf_history__ >/dev/null; then
  bind -x '"\C-h":__fzf_history__'
fi

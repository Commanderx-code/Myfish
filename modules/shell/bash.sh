# shellcheck shell=bash
# Bash Readline bindings. Load after fzf and the shared helpers.
case $- in *i*) ;; *) return ;; esac
bind -x '"\C-p":fdi'
bind -x '"\C-f":rgi'
# fzf's Ctrl-R history search stays; **Tab uses fzf completion.
bind 'set colored-stats on'
bind 'set completion-ignore-case on'

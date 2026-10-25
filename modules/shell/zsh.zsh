# Zsh ZLE widgets. Load after fzf and the shared helpers.
[[ -o interactive ]] || return
# ZLE widgets run with stdin on /dev/null; the prompt and the editor need the terminal.
_commander_open_widget() { zle -I; fdi </dev/tty; zle reset-prompt; }
_commander_search_widget() { zle -I; rgi </dev/tty; zle reset-prompt; }
zle -N commander-open _commander_open_widget
zle -N commander-search _commander_search_widget
bindkey '^P' commander-open
bindkey '^F' commander-search

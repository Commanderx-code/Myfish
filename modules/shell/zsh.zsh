# Zsh ZLE widgets. Load after fzf and the shared helpers.
[[ -o interactive ]] || return
_commander_open_widget() { zle -I; fdi; zle reset-prompt; }
_commander_search_widget() { zle -I; rgi; zle reset-prompt; }
zle -N commander-open _commander_open_widget
zle -N commander-search _commander_search_widget
bindkey '^P' commander-open
bindkey '^F' commander-search

if (( $+widgets[fzf-history-widget] )); then bindkey '^H' fzf-history-widget; fi

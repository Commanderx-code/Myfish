# Listing shortcuts. The workstation dotfiles import this file as it is.
status is-interactive; or return
# Without eza, ls and tree keep their usual meaning.
command -q eza; or return

# Replacements
alias ls="eza --icons --group-directories-first"
alias ll="eza -lh --icons --group-directories-first --time-style=long-iso"
alias la="eza -lha --icons --group-directories-first"
alias tree="eza --tree --level=2 --icons"

# Sort variations
alias lx="eza -lh --sort=extension --icons"
alias lk="eza -lh --sort=size --icons"
alias lt="eza -lh --sort=modified --icons"

# Directories / files only
alias ldir="eza -l --icons --only-dirs"
alias lf="eza -l --icons --only-files"

alias lgit="eza -l --git --icons"
alias l1="eza -1 --icons"
alias lr="eza -R --icons"

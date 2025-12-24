# ---------------------------------------------------------
# EZA - Modern ls Replacement
# ---------------------------------------------------------

# Colors
set -x EZA_COLORS \
"da=1;34:\
di=1;36:\
fi=0;37:\
ex=1;32:\
*.zip=1;31:\
*.tar=1;31:\
*.gz=1;31:\
*.jpg=1;35:\
*.png=1;35"

# Replacements
alias ls="eza --icons --group-directories-first --colour=always"
alias ll="eza -lh --icons --group-directories-first --time-style=long-iso"
alias la="eza -lha --icons --group-directories-first"
alias tree="eza --tree --level=2 --icons"

# Sort variations
alias lx="eza -lh --sort=extension --icons"
alias lk="eza -lh --sort=size --icons"
alias lt="eza -lh --sort=modified --icons"

# Directories / files only
alias ldir="eza -l --icons --filter=dir"
alias lf="eza -l --icons --filter=file"

alias lg="eza -l --git --icons"
alias l1="eza -1 --icons"
alias lr="eza -R --icons"

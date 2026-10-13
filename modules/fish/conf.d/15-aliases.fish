# Everyday aliases and abbreviations. The workstation dotfiles import this
# file as it is, so keep machine-specific shortcuts out of it.
status is-interactive; or return
alias cp 'cp -i'
alias mv 'mv -i'
if command -q trash
    alias rm 'trash -v'
end
# Replace a command only when its replacement is here; the c-prefixed
# names always reach the original.
alias ccat 'command cat'
alias cgrep 'command grep'
alias cfind 'command find'
if command -q bat; or functions -q bat
    alias cat bat
end
if command -q rg
    alias grep rg
end
if command -q fd; or functions -q fd
    alias find fd
end
alias cls clear
if test (uname -s) = Darwin
    alias psa 'ps aux'
    alias mountedinfo 'df -h'
else
    alias psa 'ps auxf'
    alias mountedinfo 'df -hT'
end
alias da 'date "+%Y-%m-%d %A %T %Z"'
abbr -a .. 'cd ..'
abbr -a ... 'cd ../..'
abbr -a .... 'cd ../../..'
abbr -a ..... 'cd ../../../..'
abbr -a bd 'cd -'
abbr -a home 'cd ~'

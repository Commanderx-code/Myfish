# Interactive customizations only; scripts keep normal command behavior.
if not status is-interactive
    return
end
set -g fish_greeting
if command -q nvim
    alias vim nvim
end
# Debian names these executables differently.
if not command -q bat; and command -q batcat
    function bat --wraps batcat
        command batcat $argv
    end
end
if not command -q fd; and command -q fdfind
    function fd --wraps fdfind
        command fdfind $argv
    end
end
alias cp 'cp -i'
alias mv 'mv -i'
if command -q trash
    alias rm 'trash -v'
end
alias cat bat
alias ccat 'command cat'
alias grep rg
alias cgrep 'command grep'
alias find fd
alias cfind 'command find'
alias cls clear
if test (uname -s) = Darwin
    alias psa 'ps aux'
    alias mountedinfo 'df -h'
else
    alias psa 'ps auxf'
    alias mountedinfo 'df -hT'
end
alias da 'date "+%Y-%m-%d %A %T %Z"'
alias gs 'git status'
alias ga 'git add'
alias gc 'git commit'
alias gp 'git push'
alias gl 'git pull'
if command -q lazygit
    alias lg lazygit
end
abbr -a .. 'cd ..'
abbr -a ... 'cd ../..'
abbr -a .... 'cd ../../..'
abbr -a ..... 'cd ../../../..'
abbr -a bd 'cd -'
abbr -a home 'cd ~'

# Search defaults; no forced sixel output unless the user opens a preview.
set -l finder fd
command -q fd; or set finder fdfind
set -q FZF_DEFAULT_COMMAND; or set -gx FZF_DEFAULT_COMMAND "$finder --type f --hidden --exclude .git --exclude node_modules --exclude .cache"
set -q FZF_CTRL_T_COMMAND; or set -gx FZF_CTRL_T_COMMAND "$FZF_DEFAULT_COMMAND"
set -q FZF_ALT_C_COMMAND; or set -gx FZF_ALT_C_COMMAND "$finder --type d --hidden --exclude .git --exclude node_modules --exclude .cache"
set -l preview 'bash '(string escape -- "$HOME/.local/bin/fzf-preview")' {}'
set -q FZF_DEFAULT_OPTS; or set -gx FZF_DEFAULT_OPTS '--layout=reverse --border --ansi --preview-window=right,60%,nowrap --bind=ctrl-/:toggle-preview'
set -q FZF_CTRL_T_OPTS; or set -gx FZF_CTRL_T_OPTS '--preview='(string escape -- "$preview")

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
alias gs 'git status'
alias ga 'git add'
alias gc 'git commit'
alias gp 'git push'
alias gl 'git pull'
if command -q lazygit
    alias lg lazygit
end
# Search defaults; no forced sixel output unless the user opens a preview.
# Without fd, fzf's own walker lists files.
if command -q fd; or command -q fdfind
    set -l finder fd
    command -q fd; or set finder fdfind
    set -l excludes --hidden --exclude .git --exclude node_modules --exclude .cache
    set -q FZF_DEFAULT_COMMAND; or set -gx FZF_DEFAULT_COMMAND "$finder --type f $excludes"
    # fzf's widgets evaluate these in fish with $dir set to the typed directory.
    # They stay unexported because other shells run them without $dir.
    set -q FZF_CTRL_T_COMMAND; or set -g FZF_CTRL_T_COMMAND "$finder --type f $excludes --search-path \"\$dir\""
    set -q FZF_ALT_C_COMMAND; or set -g FZF_ALT_C_COMMAND "$finder --type d $excludes --search-path \"\$dir\""
end
set -l preview 'bash '(string escape -- "$HOME/.local/bin/fzf-preview")' {}'
set -q FZF_DEFAULT_OPTS; or set -gx FZF_DEFAULT_OPTS '--layout=reverse --border --ansi --preview-window=right,60%,nowrap --bind=ctrl-/:toggle-preview'
set -q FZF_CTRL_T_OPTS; or set -gx FZF_CTRL_T_OPTS '--preview='(string escape -- "$preview")

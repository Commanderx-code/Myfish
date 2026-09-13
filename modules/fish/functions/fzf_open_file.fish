function fzf_open_file --description "FZF pick a file and open in nvim"
    if not command -q fzf
        echo "fzf not installed"
        return 1
    end

    if not type -q fd
        echo "fd not installed"
        return 1
    end

    set -l preview "$HOME/.local/bin/fzf-preview"

    if not test -x "$preview"
        echo "fzf preview script missing:"
        echo "$preview"
        return 1
    end

    set -l file (
        fd --type f --hidden --follow \
            --exclude .git \
            --exclude node_modules \
            --exclude .cache \
            --exclude .cargo \
            --exclude go/pkg/mod \
            --exclude .local/share \
            2>/dev/null |
        fzf \
            --layout=reverse \
            --border \
            --ansi \
            --preview-window='right,60%,nowrap' \
            --preview="bash "(string escape -- "$preview")" {}" \
            --bind='ctrl-/:toggle-preview'
    )

    test -z "$file"; and return

    set -l editor (__commander_editor); or return
    commandline -r -- (string join ' ' -- $editor (string escape -- $file))
    commandline -f execute
end

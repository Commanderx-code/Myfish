function fzf_open_file --description "Pick a file with fzf and open it in an editor"
    if not command -q fzf
        echo "fzf not installed" >&2
        return 1
    end

    if not command -q fd; and not command -q fdfind
        echo "fd not installed" >&2
        return 1
    end

    set -l preview "$HOME/.local/bin/fzf-preview"

    if not test -x "$preview"
        echo "fzf preview script missing: $preview" >&2
        return 1
    end

    set -l file (
        __commander_find --type f --hidden --follow --print0 \
            --exclude .git \
            --exclude node_modules \
            --exclude .cache \
            --exclude .cargo \
            --exclude go/pkg/mod \
            --exclude .local/share \
            2>/dev/null |
        command fzf --read0 --print0 \
            --layout=reverse \
            --border \
            --ansi \
            --preview-window='right,60%,nowrap' \
            --preview="bash "(string escape -- "$preview")" {}" \
            --bind='ctrl-/:toggle-preview' | string split0
    )

    test (count $file) -eq 1; or return 0

    set -l editor (__commander_editor); or return
    # The -- keeps a file whose name starts with - or + from being read as an editor option.
    commandline -r -- (string join ' ' -- $editor -- (string escape -- $file))
    commandline -f execute
end

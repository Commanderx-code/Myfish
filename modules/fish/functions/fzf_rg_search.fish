function fzf_rg_search --description "Search text with ripgrep + fzf and open result in nvim"
    if not command -q rg
        echo "ripgrep is not installed"
        return 1
    end

    if not command -q fzf
        echo "fzf is not installed"
        return 1
    end

    set -l q
    read -l -P "Search text: " q

    test -z "$q"; and return 0

    set -l pick (
        "$HOME/.local/bin/fzf-rg" \
            --glob '!.git/*' \
            --glob '!node_modules/*' \
            --glob '!.cache/*' \
            --glob '!.local/share/Trash/*' \
            --glob '!.local/share/Steam/*' \
            -- "$q" "$PWD" | string split0
    )

    test (count $pick) -eq 2; or return 0
    set -l line "$pick[1]"
    set -l file "$pick[2]"
    string match -qr '^[1-9][0-9]*$' -- "$line"; or return 1

    if command -q nvim
        commandline -r -- (string join ' ' -- (string escape -- nvim "+$line" -- "$file"))
        commandline -f execute
    else
        echo "$file:$line"
    end
end

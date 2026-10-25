function __fzf_starstar_tab --description 'Tab: expand a trailing ** with fzf, otherwise complete'
    set -l token (commandline -t)
    if string match -qr '\*\*$' -- "$token"
        set -l base (string replace -r '\*\*$' '' -- "$token")
        commandline -t -- $base
        if functions -q fzf-file-widget
            fzf-file-widget
        else if command -q fzf
            # Without fzf's bindings, put the picked file in place of the token and keep the rest of the line.
            set -l dir (string replace -r -- '^~' $HOME (string replace -r -- '/$' '' "$base"))
            test -n "$dir"; and test -d "$dir"; or set dir .
            set -l picked (__commander_find --type f --hidden --exclude .git --print0 --search-path $dir 2>/dev/null |
                command fzf --read0 --print0 | string split0)
            if test (count $picked) -eq 1
                commandline -t -- (string escape -- $picked)
            end
            commandline -f repaint
        end
        return
    end
    commandline -f complete
end

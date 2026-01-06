function fzf_rg_search
    if not command -q fzf
        echo "fzf not installed"
        return 1
    end
    if not command -q rg
        echo "ripgrep (rg) not installed (install: sudo apt install ripgrep)"
        return 1
    end

    set -l q (commandline -t)
    if test -z "$q"
        echo -n "rg> "
        read -l q
    end
    test -z "$q"; and return

    set -l pick (rg --line-number --no-heading --smart-case --color=always "$q" 2>/dev/null \
        | fzf --ansi --height 80% --layout=reverse --border \
              --delimiter ':' \
              --preview '__preview_file {1} {2}' \
              --preview-window='right,60%,wrap')

    test -z "$pick"; and return

    set -l file (echo "$pick" | cut -d: -f1)
    set -l line (echo "$pick" | cut -d: -f2)

    commandline -r "nvim +$line '$file'"
    commandline -f execute
end

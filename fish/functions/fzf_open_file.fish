function fzf_open_file
    if not command -q fzf
        echo "fzf not installed"
        return 1
    end

    # Use fd (your wrapper is fine). If you ever remove it, fd binary still exists too.
    set -l file (fd --type f --hidden --follow --exclude .git 2>/dev/null \
        | fzf --height 80% --layout=reverse --border \
              --preview '__preview_file {}' \
              --preview-window='right,60%,wrap')

    test -n "$file"; and commandline -r "nvim '$file'"; and commandline -f execute
end

function fcd
    set dir (eza -D --colour=always | fzf)
    if test -n "$dir"
        cd $dir
    end
end

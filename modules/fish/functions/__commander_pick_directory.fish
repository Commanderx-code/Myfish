function __commander_pick_directory --description 'Pick a directory using the supplied fd options'
    command -q fzf; or begin
        echo 'Install fzf to use this picker.' >&2
        return 127
    end
    set -l directory (__commander_find --type d --print0 $argv | command fzf --read0 --print0 | string split0)
    set -l results $pipestatus
    test $results[1] -eq 0; or return $results[1]
    test (count $directory) -eq 1; or return 0
    cd -- "$directory"
end

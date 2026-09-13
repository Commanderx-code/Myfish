function fcd --description 'Fuzzy directory navigation'
    set -l finder fd
    command -q fd; or set finder fdfind
    set -l directory ($finder --type d --hidden --exclude .git --print0 | fzf --read0 --print0 | string split0)
    test (count $directory) -eq 1; and cd -- "$directory"
end

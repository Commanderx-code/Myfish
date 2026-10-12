function gcom --description 'Stage everything here and commit with the given message'
    if test (count $argv) -eq 0
        echo "Usage: gcom <message>" >&2
        return 1
    end
    git add .; or return $status
    git commit -m (string join ' ' -- $argv)
end

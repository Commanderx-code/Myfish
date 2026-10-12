function gcom
    if test (count $argv) -eq 0
        echo "Usage: gcom <message>"
        return 1
    end
    git add .; or return $status
    git commit -m (string join ' ' -- $argv)
end

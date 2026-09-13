function lazyg --description 'Stage, commit and push; stop on any error'
    if test (count $argv) -eq 0
        echo 'Usage: lazyg <message>' >&2
        return 1
    end
    gcom $argv; and git push
end

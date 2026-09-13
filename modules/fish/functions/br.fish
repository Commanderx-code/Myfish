function br --wraps broot
    command -q broot; or begin
        echo 'Install broot to use br.' >&2
        return 1
    end
    set -l output (mktemp); or return
    command broot --outcmd "$output" $argv
    set -l result $status
    if test $result -eq 0
        source "$output"
        set result $status
    end
    command rm -f -- "$output"
    return $result
end

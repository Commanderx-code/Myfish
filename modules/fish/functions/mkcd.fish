function mkcd --description 'Create and enter a directory'
    if test (count $argv) -ne 1
        echo 'Usage: mkcd <directory>' >&2
        return 1
    end
    command mkdir -p -- "$argv[1]"; and cd -- "$argv[1]"
end

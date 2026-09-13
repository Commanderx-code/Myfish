function serve --description 'Serve the current directory on localhost'
    set -l port 8000
    if test (count $argv) -gt 0
        set port "$argv[1]"
    end
    python3 -m http.server --bind 127.0.0.1 "$port"
end

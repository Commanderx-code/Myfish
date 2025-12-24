function serve
    set port (or $argv[1] 8000)
    python3 -m http.server $port
end

function psg
    if test (count $argv) -lt 1
        echo "Usage: psg <pattern>"
        return 1
    end

    if command -q pgrep
        pgrep -ai -- $argv[1]
    else
        ps aux | rg -i -- $argv[1]
    end
end

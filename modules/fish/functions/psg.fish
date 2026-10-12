function psg
    if test (count $argv) -lt 1
        echo "Usage: psg <pattern>"
        return 1
    end

    if command -q pgrep
        if test (uname -s) = Darwin
            pgrep -ifl -- $argv[1]
        else
            pgrep -ai -- $argv[1]
        end
    else
        ps aux | rg -i -- $argv[1]
    end
end

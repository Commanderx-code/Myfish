function psg
    ps aux | grep -i $argv[1] | grep -v grep
end

function __commander_find --description 'Run fd under its platform-specific executable name'
    if command -q fd
        command fd $argv
    else if command -q fdfind
        command fdfind $argv
    else
        echo 'Install fd (fd-find on Debian) to use this picker.' >&2
        return 127
    end
end

function __commander_editor --description 'Print the first available editor'
    for editor in nvim vim nano vi
        if command -q $editor
            echo $editor
            return 0
        end
    end
    echo 'No supported editor found' >&2
    return 1
end

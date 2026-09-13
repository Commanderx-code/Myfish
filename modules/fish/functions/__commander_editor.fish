function __commander_editor
    for editor in nvim vim nano vi
        if command -q $editor
            echo $editor
            return 0
        end
    end
    echo 'No supported editor found' >&2
    return 1
end

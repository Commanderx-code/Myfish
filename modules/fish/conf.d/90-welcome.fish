if status is-interactive; and not set -q COMMANDER_QUIET
    set -l greeting_file "$HOME/.config/commander-os/greeting.txt"
    if set -q XDG_CONFIG_HOME; and test -n "$XDG_CONFIG_HOME"
        set greeting_file "$XDG_CONFIG_HOME/commander-os/greeting.txt"
    end
    if test -f "$greeting_file"
        set -l greeting (string collect < "$greeting_file")
        if test -n "$greeting"
            printf '%s\n' "$greeting"
        end
    else
        printf 'Hello, %s ⚡\n' (whoami)
    end
    if command -q fastfetch
        fastfetch
    end
end

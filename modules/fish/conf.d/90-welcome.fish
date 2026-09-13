if status is-interactive; and not set -q COMMANDER_QUIET
    printf 'Hello, %s ⚡\n' (whoami)
    if command -q fastfetch
        fastfetch
    end
end

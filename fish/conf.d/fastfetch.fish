# Greeting + fastfetch for every interactive shell in Konsole

if status is-interactive
    if set -q KONSOLE_VERSION

        # Greeting (bold, Nerd Font lightning bolt)
        set_color
	printf "Hello, Commander "
	set_color yellow
	echo ""
	set_color normal

	# Fastfetch
        if command -v fastfetch >/dev/null
            fastfetch
        end

    end
end

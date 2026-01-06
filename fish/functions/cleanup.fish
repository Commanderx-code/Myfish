function cleanup --description "Clean caches and remove unused packages"
    if command -v nala >/dev/null
        sudo nala autoremove -y
        sudo nala clean
    else
        sudo apt autoremove -y
        sudo apt autoclean
        sudo apt clean
    end

    if command -v flatpak >/dev/null
        flatpak uninstall --unused -y
    end

    if command -v journalctl >/dev/null
        # keep last 7 days of logs (safe default)
        sudo journalctl --vacuum-time=7d >/dev/null 2>&1
    end
end

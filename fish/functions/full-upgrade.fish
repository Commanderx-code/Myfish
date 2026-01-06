function full-upgrade --description "Full system upgrade (nala/apt + flatpak + snap + topgrade)"
    echo " Running system upgrade..."

    # --- System packages ---
    if command -v nala >/dev/null
        sudo nala full-upgrade -y
    else
        sudo apt full-upgrade -y
    end

    # --- Flatpak ---
    if command -v flatpak >/dev/null
        echo "📦 Updating Flatpaks..."
        flatpak update -y
    end

    # --- Snap ---
    if command -v snap >/dev/null
        echo "📦 Updating Snaps..."
        sudo snap refresh
    end

    # --- Topgrade (run last) ---
    if command -v topgrade >/dev/null
        echo "  Running Topgrade..."
        topgrade
    else
        echo "ℹ️ Topgrade not installed — skipping"
    end

    echo " Full upgrade complete"
end

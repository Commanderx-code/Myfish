function upgrade --description "Upgrade packages (nala) + flatpak"
    if command -v nala >/dev/null
        sudo nala upgrade -y
    else
        sudo apt upgrade -y
    end
    if command -v flatpak >/dev/null
        flatpak update -y
    end
end

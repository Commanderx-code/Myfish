function update --description "Update package lists (nala) + flatpak"
    if command -v nala >/dev/null
        sudo nala update
    else
        echo "nala not found; falling back to apt"
        sudo apt update
    end
    if command -v flatpak >/dev/null
        flatpak update -y
    end
end

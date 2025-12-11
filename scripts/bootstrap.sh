#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"

echo "[+] Starting full system rebuild..."

# -----------------------------
# Install dependencies
# -----------------------------
echo "[+] Installing core packages..."
if command -v nala >/dev/null 2>&1; then
    sudo nala install -y git fish curl flatpak
else
    sudo apt install -y git fish curl flatpak
fi

# -----------------------------
# Restore Fish config
# -----------------------------
echo "[+] Restoring Fish configuration..."
mkdir -p ~/.config/fish
cp -r "$REPO/fish/"* ~/.config/fish/

# -----------------------------
# Restore Starship
# -----------------------------
echo "[+] Restoring Starship config..."
mkdir -p ~/.config
cp "$REPO/starship.toml" ~/.config/

# -----------------------------
# Restore Ranger config
# -----------------------------
echo "[+] Restoring Ranger configuration..."
mkdir -p ~/.config/ranger
cp -r "$REPO/ranger/"* ~/.config/ranger/

# -----------------------------
# Restore Fastfetch config
# -----------------------------
echo "[+] Restoring Fastfetch..."
mkdir -p ~/.config/fastfetch
cp "$REPO/fastfetch/config.jsonc" ~/.config/fastfetch/

# -----------------------------
# Install Homebrew if missing
# -----------------------------
if ! command -v brew >/dev/null 2>&1; then
    echo "[+] Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Add brew to PATH
if ! grep -q "linuxbrew" ~/.config/fish/config.fish; then
    echo 'fish_add_path /home/linuxbrew/.linuxbrew/bin /home/linuxbrew/.linuxbrew/sbin' >> ~/.config/fish/config.fish
fi

# -----------------------------
# Install Brew packages
# -----------------------------
if [ -f "$REPO/brew_packages.txt" ]; then
    echo "[+] Installing Brew packages..."
    while read pkg; do
        [[ -n "$pkg" ]] && brew install "$pkg"
    done < "$REPO/brew_packages.txt"
fi

# -----------------------------
# Install Flatpaks
# -----------------------------
if [ -f "$REPO/flatpaks.txt" ]; then
    echo "[+] Installing Flatpak applications..."
    while read pkg; do
        [[ -n "$pkg" ]] && flatpak install -y "$pkg"
    done < "$REPO/flatpaks.txt"
fi

# -----------------------------
# Restore Secrets (WiFi, SSH, etc.)
# -----------------------------
if [ -f "$REPO/secrets/ObiLan.nmconnection.gpg" ]; then
    echo "[+] Decrypting WiFi secrets..."
    gpg --decrypt "$REPO/secrets/ObiLan.nmconnection.gpg" > ~/MyFish/secrets_plain/ObiLan.nmconnection
    sudo cp ~/MyFish/secrets_plain/ObiLan.nmconnection /etc/NetworkManager/system-connections/
    sudo chmod 600 /etc/NetworkManager/system-connections/ObiLan.nmconnection
    sudo nmcli connection reload
fi

echo "[✓] Full rebuild complete!"


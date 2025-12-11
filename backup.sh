#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"

echo "[+] Backing up configs..."

# Fish
mkdir -p "$REPO/fish"
cp -r ~/.config/fish/* "$REPO/fish/"

# Ranger
mkdir -p "$REPO/ranger"
cp -r ~/.config/ranger/* "$REPO/ranger/"

# Fastfetch
mkdir -p "$REPO/fastfetch"
cp -r ~/.config/fastfetch/* "$REPO/fastfetch/"

# Starship
cp ~/.config/starship.toml "$REPO/starship.toml"

# Brew packages
brew leaves > "$REPO/brew_packages.txt"

# Flatpaks
flatpak list --app --columns=application > "$REPO/flatpaks.txt"

# Secrets
echo "[+] Encrypting secrets..."
mkdir -p "$REPO/secrets"
gpg --yes --output "$REPO/secrets/ObiLan.nmconnection.gpg" \
    --symmetric ~/MyFish/secrets_plain/ObiLan.nmconnection

echo "[✓] Backup complete!"

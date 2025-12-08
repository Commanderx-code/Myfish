#!/usr/bin/env bash
set -e

echo "🔁 Restoring terminal environment..."

# Install base tools
sudo apt update
sudo apt install -y fish nala git curl fzf fastfetch flatpak snapd

# Install user packages
if [ -f packages.txt ]; then
  sudo xargs -a packages.txt nala install -y
fi

# Install flatpaks
if [ -f flatpaks.txt ]; then
  xargs -a flatpaks.txt flatpak install -y flathub
fi

# Install snaps
if [ -f snaps.txt ]; then
  sudo xargs -a snaps.txt snap install
fi

# Restore configs
mkdir -p ~/.config/fish
mkdir -p ~/.config/starship
mkdir -p ~/.config/fastfetch/logos

cp fish/config.fish ~/.config/fish/config.fish
cp starship/starship.toml ~/.config/starship/starship.toml
cp fastfetch/config.jsonc ~/.config/fastfetch/config.jsonc
cp fastfetch/zorin.png ~/.config/fastfetch/logos/zorin.png

# Set fish as default shell
chsh -s /usr/bin/fish

echo "✅ Restore complete. Reboot or log out for full effect."

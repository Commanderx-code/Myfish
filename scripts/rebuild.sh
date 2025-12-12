#!/usr/bin/env bash
set -e

echo "[INFO] Rebuilding system..."

sudo apt update
sudo apt install -y \
  fish starship fastfetch ranger fzf \
  nala git curl zenity gpg

echo "[INFO] Restoring configs..."
cp -r ~/MyFish/fish ~/.config/
cp ~/MyFish/starship.toml ~/.config/

echo "[INFO] Rebuild complete"


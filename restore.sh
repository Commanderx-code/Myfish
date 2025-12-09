#!/usr/bin/env bash

set -e

REPO_URL="git@github.com:Commanderx-code/Myfish.git"
REPO_DIR="$HOME/MyFish"
CONFIG_DIR="$HOME/.config"

echo "=============================="
echo " MyFish One-Command Restore"
echo "=============================="

# -----------------------------
# 1. Install base dependencies
# -----------------------------

echo "[+] Installing base packages..."

if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y \
        git fish curl wget \
        ranger eza fzf \
        highlight atool ueberzug \
        ffmpegthumbnailer poppler-utils imagemagick \
        bat zoxide
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm \
        git fish curl wget \
        ranger eza fzf \
        highlight atool ueberzug \
        ffmpegthumbnailer poppler imagemagick \
        bat zoxide
else
    echo "Unsupported package manager"
    exit 1
fi

# -----------------------------
# 2. Clone MyFish repository
# -----------------------------

if [ ! -d "$REPO_DIR" ]; then
    echo "[+] Cloning MyFish repo..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "[+] MyFish repo already exists. Pulling updates..."
    cd "$REPO_DIR"
    git pull
fi

# -----------------------------
# 3. Restore configuration files
# -----------------------------

echo "[+] Restoring configuration files..."

mkdir -p "$CONFIG_DIR/fish"
mkdir -p "$CONFIG_DIR/ranger"

cp -r "$REPO_DIR/fish/"* "$CONFIG_DIR/fish/"
cp -r "$REPO_DIR/ranger/"* "$CONFIG_DIR/ranger/"
cp "$REPO_DIR/starship.toml" "$CONFIG_DIR/starship.toml"

# -----------------------------
# 4. Set Fish as default shell
# -----------------------------

echo "[+] Setting Fish as default shell..."
if ! grep -q "$(which fish)" /etc/shells; then
    echo "$(which fish)" | sudo tee -a /etc/shells
fi
chsh -s "$(which fish)"

# -----------------------------
# 5. Final reload
# -----------------------------

echo "[+] Restore complete."
echo "[!] Please log out and log back in for Fish to become default."
echo "[✓] MyFish environment restored successfully."

#!/usr/bin/env bash
set -e

REPO_DIR="$HOME/MyFish"
CONFIG_DIR="$HOME/.config"

echo "=============================="
echo "   MyFish Cross-Distro Restore"
echo "=============================="

# -----------------------------
# Detect Distro / Package Manager
# -----------------------------

if command -v apt >/dev/null 2>&1 || command -v nala >/dev/null 2>&1; then
    DISTRO="debian"
elif command -v pacman >/dev/null 2>&1; then
    DISTRO="arch"
else
    echo "❌ Unsupported distro / package manager"
    exit 1
fi

echo "[+] Detected distro: $DISTRO"

# -----------------------------
# Install Packages
# -----------------------------

install_debian() {
    echo "[+] Installing packages (Debian/Ubuntu/Zorin)..."
    sudo apt update
    sudo apt install -y \
        git fish curl wget \
        ranger eza fzf \
        highlight atool ueberzug \
        ffmpegthumbnailer poppler-utils imagemagick \
        bat zoxide fastfetch
}

install_arch() {
    echo "[+] Installing packages (Arch/Garuda)..."
    sudo pacman -Sy --noconfirm \
        git fish curl wget \
        ranger eza fzf \
        highlight atool ueberzug \
        ffmpegthumbnailer poppler imagemagick \
        bat zoxide fastfetch
}

case "$DISTRO" in
    debian) install_debian ;;
    arch)   install_arch ;;
esac

# -----------------------------
# Restore Configurations
# -----------------------------

echo "[+] Restoring configuration files..."

mkdir -p "$CONFIG_DIR/fish"
mkdir -p "$CONFIG_DIR/ranger"

cp -r "$REPO_DIR/fish/"* "$CONFIG_DIR/fish/"
cp -r "$REPO_DIR/ranger/"* "$CONFIG_DIR/ranger/"
cp "$REPO_DIR/starship.toml" "$CONFIG_DIR/starship.toml"

# -----------------------------
# Set Fish as Default Shell
# -----------------------------

echo "[+] Setting Fish as default shell..."

if ! grep -q "$(which fish)" /etc/shells; then
    echo "$(which fish)" | sudo tee -a /etc/shells
fi

chsh -s "$(which fish)"

# -----------------------------
# Final Message
# -----------------------------

echo ""
echo "✅ Restore complete on $DISTRO."
echo "⚠️ Please log out and log back in to activate Fish."
echo "🎉 MyFish environment restored successfully."


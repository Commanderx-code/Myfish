#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"

echo "[+] Restoring system from $REPO"

# -----------------------------
# Fish configuration
# -----------------------------
echo "[+] Restoring Fish configuration..."
mkdir -p ~/.config/fish
cp "$REPO/configs/fish/config.fish" ~/.config/fish/ 2>/dev/null || true
cp "$REPO/configs/fish/fish_plugins" ~/.config/fish/ 2>/dev/null || true

mkdir -p ~/.config/fish/conf.d ~/.config/fish/functions ~/.config/fish/completions
cp -r "$REPO/configs/fish/conf.d/"* ~/.config/fish/conf.d/ 2>/dev/null || true
cp -r "$REPO/configs/fish/functions/"* ~/.config/fish/functions/ 2>/dev/null || true
cp -r "$REPO/configs/fish/completions/"* ~/.config/fish/completions/ 2>/dev/null || true

# -----------------------------
# Fastfetch, Ranger, Starship
# -----------------------------
echo "[+] Restoring Fastfetch..."
mkdir -p ~/.config/fastfetch
cp -r "$REPO/configs/fastfetch/"* ~/.config/fastfetch/ 2>/dev/null || true

echo "[+] Restoring Ranger..."
mkdir -p ~/.config/ranger
cp -r "$REPO/configs/ranger/"* ~/.config/ranger/ 2>/dev/null || true

echo "[+] Restoring Starship..."
mkdir -p ~/.config
cp "$REPO/configs/starship.toml" ~/.config/starship.toml 2>/dev/null || true

# -----------------------------
# Themes / Icons / Fonts
# -----------------------------
echo "[+] Restoring themes/icons/fonts..."
mkdir -p ~/.themes ~/.icons ~/.local/share/fonts

cp -r "$REPO/configs/themes/"* ~/.themes/ 2>/dev/null || true
cp -r "$REPO/configs/icons/"* ~/.icons/ 2>/dev/null || true
cp -r "$REPO/configs/fonts/"* ~/.local/share/fonts/ 2>/dev-null || true

fc-cache -f ~/.local/share/fonts ~/.fonts 2>/dev/null || true

# -----------------------------
# systemd user units
# -----------------------------
echo "[+] Restoring user systemd units..."
mkdir -p ~/.config/systemd/user
cp -r "$REPO/systemd/user/"* ~/.config/systemd/user/ 2>/dev/null || true
systemctl --user daemon-reload || true
systemctl --user enable --now autosync.timer 2>/dev/null || true

# -----------------------------
# Secrets (WiFi + SSH)
# -----------------------------
if [ -x "$REPO/scripts/secrets_decrypt.sh" ]; then
    echo "[+] Restoring secrets (WiFi/SSH)..."
    "$REPO/scripts/secrets_decrypt.sh"
fi

# -----------------------------
# Packages
# -----------------------------
echo "[+] Restoring APT/Nala packages..."
if [ -f "$REPO/pkgs/packages.txt" ]; then
    if command -v nala >/dev/null 2>&1; then
        xargs -a "$REPO/pkgs/packages.txt" sudo nala install -y || true
    else
        xargs -a "$REPO/pkgs/packages.txt" sudo apt install -y || true
    fi
fi

if command -v brew >/dev/null 2>&1 && [ -f "$REPO/pkgs/brew_packages.txt" ]; then
    echo "[+] Restoring Homebrew packages..."
    while read pkg; do
        [[ -n "$pkg" ]] && brew install "$pkg"
    done < "$REPO/pkgs/brew_packages.txt"
fi

if command -v flatpak >/dev/null 2>&1 && [ -f "$REPO/pkgs/flatpaks.txt" ]; then
    echo "[+] Restoring Flatpak apps..."
    while read pkg; do
        [[ -n "$pkg" ]] && flatpak install -y "$pkg"
    done < "$REPO/pkgs/flatpaks.txt"
fi

echo "[✓] Restore complete."


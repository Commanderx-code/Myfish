#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"

echo "[+] Starting full organized backup..."

# -------------------------------------------------------------------
# Make folder structure if missing
# -------------------------------------------------------------------

mkdir -p "$REPO/configs/fish/conf.d"
mkdir -p "$REPO/configs/fish/functions"
mkdir -p "$REPO/configs/fish/completions"
mkdir -p "$REPO/configs/fastfetch"
mkdir -p "$REPO/configs/ranger"
mkdir -p "$REPO/configs/themes"
mkdir -p "$REPO/configs/icons"
mkdir -p "$REPO/configs/fonts"

mkdir -p "$REPO/pkgs"
mkdir -p "$REPO/secrets/plain"
mkdir -p "$REPO/secrets/encrypted"
mkdir -p "$REPO/systemd/user"

# -------------------------------------------------------------------
# FISH CONFIG BACKUP
# -------------------------------------------------------------------
echo "[+] Backing up Fish configuration..."

cp ~/.config/fish/config.fish "$REPO/configs/fish/" 2>/dev/null || true
cp ~/.config/fish/fish_plugins "$REPO/configs/fish/" 2>/dev/null || true

cp -r ~/.config/fish/conf.d/* "$REPO/configs/fish/conf.d/" 2>/dev/null || true
cp -r ~/.config/fish/functions/* "$REPO/configs/fish/functions/" 2>/dev/null || true
cp -r ~/.config/fish/completions/* "$REPO/configs/fish/completions/" 2>/dev/null || true

# -------------------------------------------------------------------
# RANGER, FASTFETCH, STARSHIP
# -------------------------------------------------------------------
echo "[+] Backing up Fastfetch..."
cp -r ~/.config/fastfetch/* "$REPO/configs/fastfetch/" 2>/dev/null || true

echo "[+] Backing up Ranger..."
cp -r ~/.config/ranger/* "$REPO/configs/ranger/" 2>/dev/null || true

echo "[+] Backing up Starship..."
cp ~/.config/starship.toml "$REPO/configs/starship.toml" 2>/dev/null || true

# -------------------------------------------------------------------
# THEMES / ICONS / FONTS
# -------------------------------------------------------------------
echo "[+] Backing up themes/icons/fonts..."

cp -r ~/.themes/* "$REPO/configs/themes/" 2>/dev/null || true
cp -r ~/.icons/* "$REPO/configs/icons/" 2>/dev/null || true
cp -r ~/.local/share/fonts/* "$REPO/configs/fonts/" 2>/dev/null || true

# -------------------------------------------------------------------
# SYSTEMD USER UNITS
# -------------------------------------------------------------------
echo "[+] Backing up systemd user units..."
cp -r ~/.config/systemd/user/* "$REPO/systemd/user/" 2>/dev/null || true

# -------------------------------------------------------------------
# PACKAGE LISTS
# -------------------------------------------------------------------
echo "[+] Saving package lists..."

dpkg --get-selections | awk '{print $1}' | sort > "$REPO/pkgs/packages.txt"

if command -v brew >/dev/null 2>&1; then
    brew leaves > "$REPO/pkgs/brew_packages.txt"
fi

if command -v flatpak >/dev/null 2>&1; then
    flatpak list --app --columns=application > "$REPO/pkgs/flatpaks.txt"
fi

# -------------------------------------------------------------------
# WIFI + SSH SECRET ENCRYPTION
# -------------------------------------------------------------------
echo "[+] Encrypting WiFi + SSH secrets..."
"$REPO/scripts/secrets_encrypt.sh"

echo "[✓] Backup complete!"

#!/usr/bin/env bash
set -euo pipefail

### CommanderOS Theme Installer
### Safe to run multiple times

REPO="$HOME/MyFish"
THEME_DIR="$REPO/themes"

echo "================================================="
echo " CommanderOS Theme Installer"
echo "================================================="

# --- helpers ---
require_sudo() {
    if [[ $EUID -ne 0 ]]; then
        echo "[INFO] Re-running with sudo..."
        exec sudo "$0" "$@"
    fi
}

log() {
    echo "[CommanderOS] $1"
}

# --- ensure root ---
require_sudo "$@"

# --- GRUB ---
install_grub_theme() {
    log "Installing GRUB theme..."
    mkdir -p /boot/grub/themes/commanderos
    cp -r "$THEME_DIR/grub/"* /boot/grub/themes/commanderos/

    if ! grep -q 'GRUB_THEME=.*commanderos/theme.txt' /etc/default/grub; then
        echo 'GRUB_THEME="/boot/grub/themes/commanderos/theme.txt"' >> /etc/default/grub
    fi

    update-grub
}

# --- Plymouth ---
install_plymouth_theme() {
    log "Installing Plymouth boot theme..."
    mkdir -p /usr/share/plymouth/themes/commanderos
    cp -r "$THEME_DIR/plymouth/"* /usr/share/plymouth/themes/commanderos/
    plymouth-set-default-theme -R commanderos || true
}

# --- SDDM ---
install_sddm_theme() {
    log "Installing SDDM login theme..."
    mkdir -p /usr/share/sddm/themes/commanderos
    cp -r "$THEME_DIR/sddm/"* /usr/share/sddm/themes/commanderos/

    mkdir -p /etc
    if [[ ! -f /etc/sddm.conf ]]; then
        cat <<EOF > /etc/sddm.conf
[Theme]
Current=commanderos
EOF
    else
        sed -i 's/^Current=.*/Current=commanderos/' /etc/sddm.conf
    fi
}

# --- Wallpapers ---
install_wallpapers() {
    log "Installing wallpapers..."
    mkdir -p /usr/share/backgrounds/commanderos
    cp "$THEME_DIR/wallpapers/default.png" \
       /usr/share/backgrounds/commanderos/default.png || true
}

# --- Konsole ---
install_konsole_theme() {
    log "Installing Konsole color scheme..."
    install -d /usr/share/konsole
    cp "$THEME_DIR/konsole/CommanderOS.colorscheme" \
       /usr/share/konsole/CommanderOS.colorscheme || true
}

# --- Kitty ---
install_kitty_theme() {
    log "Installing Kitty theme..."
    install -d /usr/share/kitty/themes
    cp "$THEME_DIR/kitty/commanderos.conf" \
       /usr/share/kitty/themes/commanderos.conf || true
}

# --- GNOME wallpaper apply (optional) ---
apply_wallpaper() {
    if command -v gsettings &>/dev/null; then
        log "Applying wallpaper (GNOME/Zorin)..."
        sudo -u "$SUDO_USER" gsettings set \
            org.gnome.desktop.background picture-uri \
            "file:///usr/share/backgrounds/commanderos/default.png" || true
    fi
}

# --- Run all ---
install_grub_theme
install_plymouth_theme
install_sddm_theme
install_wallpapers
install_konsole_theme
install_kitty_theme
apply_wallpaper

echo "================================================="
echo " CommanderOS themes installed successfully"
echo "================================================="


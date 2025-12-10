#!/usr/bin/env bash
set -e

echo "🔓 Decrypting secrets..."
~/MyFish/scripts/decrypt_secrets.sh

echo "🔧 Restoring SSH keys..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cp ~/MyFish/secrets_plain/ssh_id_rsa ~/.ssh/id_rsa 2>/dev/null || true
cp ~/MyFish/secrets_plain/ssh_id_rsa_pub ~/.ssh/id_rsa.pub 2>/dev/null || true
cp ~/MyFish/secrets_plain/ssh_config ~/.ssh/config 2>/dev/null || true
chmod 600 ~/.ssh/id_rsa 2>/dev/null || true
chmod 644 ~/.ssh/id_rsa.pub 2>/dev/null || true
chmod 600 ~/.ssh/config 2>/dev/null || true

echo "📶 Restoring Wi-Fi profiles..."
sudo cp ~/MyFish/secrets_plain/*.nmconnection /etc/NetworkManager/system-connections/ 2>/dev/null || true
sudo chmod 600 /etc/NetworkManager/system-connections/*.nmconnection 2>/dev/null || true
sudo systemctl restart NetworkManager || true

echo "🎨 Restoring Configurations..."
cp -r ~/MyFish/fish ~/.config/
cp -r ~/MyFish/fastfetch ~/.config/
cp -r ~/MyFish/ranger ~/.config/
cp ~/MyFish/starship.toml ~/.config/ 2>/dev/null || true

echo "📦 Installing APT packages..."
xargs -a ~/MyFish/packages.txt sudo nala install -y || true

echo "📦 Installing Flatpaks..."
flatpak install -y $(cat ~/MyFish/flatpaks.txt) || true

echo "📦 Installing Snaps..."
xargs -a ~/MyFish/snaps.txt sudo snap install || true

echo "🎉 System Restore Complete!"


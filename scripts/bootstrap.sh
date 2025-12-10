#!/usr/bin/env bash
set -e

echo "🚀 Installing core tools..."
sudo apt update
sudo apt install -y git fish nala flatpak snapd gpg curl wget unzip python3-pip

echo "📥 Cloning MyFish repo..."
git clone https://github.com/Commanderx-code/MyFish.git ~/MyFish

echo "🔄 Running restore..."
~/MyFish/scripts/restore.sh

echo "🐟 Setting default shell to fish..."
chsh -s /usr/bin/fish

echo "🎉 Bootstrap complete — reboot recommended!"


#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"

echo "[+] MyFish full rebuild starting..."

# Ensure base tools
echo "[+] Installing base packages (git, curl, fish, nala, flatpak, gpg)..."
sudo apt update -y
sudo apt install -y git curl fish nala flatpak gpg

# Clone repo if missing
if [ ! -d "$REPO/.git" ]; then
    echo "[+] Cloning MyFish repo..."
    git clone git@github.com:Commanderx-code/MyFish.git "$REPO" || \
    git clone https://github.com/Commanderx-code/MyFish.git "$REPO"
fi

cd "$REPO"

# Homebrew install if missing
if ! command -v brew >/dev/null 2>&1; then
    echo "[+] Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Add brew to PATH for current session
if [ -d "/home/linuxbrew/.linuxbrew/bin" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

# Run restore
"$REPO/scripts/restore.sh"

echo "[+] Setting default shell to fish (you may need to log out/in)..."
if command -v fish >/dev/null 2>&1; then
    chsh -s "$(command -v fish)" "$USER" || true
fi

echo "[✓] Rebuild complete. Open a new terminal to use your environment."

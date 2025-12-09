#!/usr/bin/env bash

set -e

REPO_URL="git@github.com:Commanderx-code/Myfish.git"
REPO_DIR="$HOME/MyFish"
LOG_FILE="$REPO_DIR/bootstrap.log"

echo "=============================="
echo "   MyFish Interactive Setup"
echo "=============================="
echo ""

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" | tee -a "$LOG_FILE"
}

confirm() {
    read -rp "$1 [y/N]: " choice
    [[ "$choice" =~ ^[Yy]$ ]]
}

# -----------------------------
# 1. Install Git & Curl
# -----------------------------
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    if confirm "Install git and curl?"; then
        log "Installing git and curl"
        sudo apt update
        sudo apt install -y git curl
    else
        log "Skipped installing git and curl"
    fi
fi

# -----------------------------
# 2. Install Nala (optional)
# -----------------------------
if ! command -v nala >/dev/null 2>&1; then
    if confirm "Install nala package manager frontend?"; then
        log "Installing nala"
        sudo apt update
        sudo apt install -y nala
    else
        log "Skipped nala installation"
    fi
fi

# -----------------------------
# 3. Setup SSH Keys (optional)
# -----------------------------
if [ ! -f "$HOME/.ssh/id_ed25519" ]; then
    if confirm "Generate SSH key for GitHub?"; then
        log "Generating SSH key"
        ssh-keygen -t ed25519 -C "myfish-setup"
        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519

        echo ""
        echo "✅ Copy this key into GitHub:"
        echo "--------------------------------"
        cat ~/.ssh/id_ed25519.pub
        echo "--------------------------------"
        echo "Add it at: https://github.com/settings/ssh/new"
        read -rp "Press ENTER after adding the key..."
    else
        log "Skipped SSH key generation"
    fi
else
    log "SSH key already exists, skipping generation"
fi

# -----------------------------
# 4. Test GitHub SSH Access
# -----------------------------
if confirm "Test SSH connection to GitHub?"; then
    log "Testing GitHub SSH connection"
    ssh -T git@github.com || true
fi

# -----------------------------
# 5. Clone or Update MyFish Repo
# -----------------------------
if [ ! -d "$REPO_DIR" ]; then
    if confirm "Clone MyFish repository now?"; then
        log "Cloning MyFish repository"
        git clone "$REPO_URL" "$REPO_DIR"
    else
        log "Skipped cloning MyFish"
        exit 0
    fi
else
    if confirm "MyFish repo exists. Pull latest updates?"; then
        log "Pulling MyFish updates"
        cd "$REPO_DIR"
        git pull
    fi
fi

# -----------------------------
# 6. Run Restore Script
# -----------------------------
if [ -f "$REPO_DIR/restore.sh" ]; then
    if confirm "Run restore.sh to install and restore your environment?"; then
        log "Running restore.sh"
        cd "$REPO_DIR"
        ./restore.sh
    else
        log "Skipped restore.sh"
    fi
else
    log "restore.sh not found in repo"
fi

# -----------------------------
# 7. Final Message
# -----------------------------
echo ""
echo "✅ Bootstrap complete."
echo "📄 Log file: $LOG_FILE"
echo "⚠️  If Fish was set as default, log out and back in."

log "Bootstrap completed successfully"


#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"
PLAIN="$REPO/secrets/plain"
ENC="$REPO/secrets/encrypted"

mkdir -p "$PLAIN" "$ENC"

echo "[+] Collecting secrets into $PLAIN"

# -----------------------------
# Wi-Fi (NetworkManager)
# -----------------------------
if [ -d /etc/NetworkManager/system-connections ]; then
    echo "[+] Copying NetworkManager .nmconnection files..."
    sudo cp /etc/NetworkManager/system-connections/*.nmconnection "$PLAIN/" 2>/dev/null || true
    sudo chown "$USER":"$USER" "$PLAIN/"*.nmconnection 2>/dev/null || true
else
    echo "[!] /etc/NetworkManager/system-connections not found, skipping WiFi copy."
fi

# -----------------------------
# SSH keys
# -----------------------------
if [ -d "$HOME/.ssh" ]; then
    echo "[+] Copying SSH files..."
    for f in id_ed25519 id_ed25519.pub id_rsa id_rsa.pub known_hosts config; do
        if [ -f "$HOME/.ssh/$f" ]; then
            cp "$HOME/.ssh/$f" "$PLAIN/$f"
        fi
    done
else
    echo "[!] ~/.ssh not found, skipping SSH copy."
fi

# -----------------------------
# Encrypt everything in secrets/plain
# -----------------------------
echo "[+] Encrypting secrets from $PLAIN into $ENC"

for f in "$PLAIN"/*; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    out="$ENC/$base.gpg"
    echo "  - Encrypting $base -> $(basename "$out")"
    gpg --yes --symmetric --cipher-algo AES256 -o "$out" "$f"
done

echo "[✓] Secrets encrypted into $ENC"

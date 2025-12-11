#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"
PLAIN="$REPO/secrets/plain"
ENC="$REPO/secrets/encrypted"

mkdir -p "$PLAIN"

echo "[+] Decrypting secrets from $ENC to $PLAIN"

for f in "$ENC"/*.gpg; do
    [ -f "$f" ] || continue
    base="$(basename "$f" .gpg)"
    out="$PLAIN/$base"
    echo "  - Decrypting $(basename "$f") -> $base"
    gpg --decrypt "$f" > "$out"
done

# -----------------------------
# Restore Wi-Fi .nmconnection
# -----------------------------
if [ -d /etc/NetworkManager/system-connections ]; then
    echo "[+] Restoring WiFi profiles..."
    for f in "$PLAIN"/*.nmconnection; do
        [ -f "$f" ] || continue
        sudo cp "$f" /etc/NetworkManager/system-connections/
    done
    sudo chmod 600 /etc/NetworkManager/system-connections/*.nmconnection 2>/dev/null || true
    sudo systemctl restart NetworkManager || true
fi

# -----------------------------
# Restore SSH
# -----------------------------
echo "[+] Restoring SSH files..."
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

for f in "$PLAIN"/id_ed25519 "$PLAIN"/id_rsa; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$HOME/.ssh/$base"
    chmod 600 "$HOME/.ssh/$base"
done

for f in "$PLAIN"/id_ed25519.pub "$PLAIN"/id_rsa.pub "$PLAIN"/known_hosts "$PLAIN"/config; do
    [ -f "$f" ] || continue
    base="$(basename "$f")"
    cp "$f" "$HOME/.ssh/$base"
    chmod 644 "$HOME/.ssh/$base"
done

echo "[✓] Secrets restored."

#!/usr/bin/env bash
set -e

SECRET_DIR="$HOME/MyFish/secrets"
PLAIN_DIR="$HOME/MyFish/secrets_plain"

declare -A SECRET_TARGETS=(
  ["ssh_id_rsa"]="$HOME/.ssh/id_rsa"
  ["ssh_id_rsa_pub"]="$HOME/.ssh/id_rsa.pub"
  ["ssh_config"]="$HOME/.ssh/config"
  ["ObiLan.nmconnection"]="/etc/NetworkManager/system-connections/ObiLan.nmconnection"
)

echo "🔓 Decrypting secrets..."

for key in "${!SECRET_TARGETS[@]}"; do
    enc_file="$SECRET_DIR/${key}.gpg"
    out_file="${SECRET_TARGETS[$key]}"

    if [[ ! -f "$enc_file" ]]; then
        echo "❌ Encrypted file missing: $enc_file"
        continue
    fi

    sudo mkdir -p "$(dirname "$out_file")"

    gpg --decrypt "$enc_file" | sudo tee "$out_file" >/dev/null
    sudo chmod 600 "$out_file"

    echo "✔ Restored: $out_file"
done

echo "🔄 Restarting NetworkManager…"
sudo systemctl restart NetworkManager


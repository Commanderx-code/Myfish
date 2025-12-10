#!/usr/bin/env bash

set -e

SECRET_DIR="$HOME/MyFish/secrets"
PLAIN_DIR="$HOME/MyFish/secrets_plain"

mkdir -p "$SECRET_DIR" "$PLAIN_DIR"

# Map of secrets to back up
declare -A SECRET_SOURCES=(
  ["ssh_id_rsa"]="$HOME/.ssh/id_rsa"
  ["ssh_id_rsa_pub"]="$HOME/.ssh/id_rsa.pub"
  ["ssh_config"]="$HOME/.ssh/config"
  ["ObiLan.nmconnection"]="/run/NetworkManager/system-connections/netplan-NM-f8121416-7c47-4d03-89e1-766b640fa85f-Obi-Lan%20Kenobi_backhaul.nmconnection"
)

echo "🔐 Encrypting secrets..."

for key in "${!SECRET_SOURCES[@]}"; do
    source_file="${SECRET_SOURCES[$key]}"
    target_enc="$SECRET_DIR/${key}.gpg"
    target_plain="$PLAIN_DIR/${key}"

    if [[ -f "$source_file" ]]; then
        sudo cp "$source_file" "$target_plain"
        sudo chown "$USER:$USER" "$target_plain"

        gpg --yes --output "$target_enc" --symmetric "$target_plain"

        echo "✔ Encrypted: $key"
    else
        echo "⚠ Skipped missing file: $source_file"
    fi
done


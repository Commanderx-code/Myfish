#!/usr/bin/env bash
set -euo pipefail

REPO="$HOME/MyFish"
BACKUP_DIR="$REPO/backups"
RESTORE_SCRIPT="$REPO/scripts/restore.sh"
DECRYPT_SCRIPT="$REPO/scripts/secrets_decrypt.sh"
REBUILD_SCRIPT="/usr/local/bin/myfish-rebuild.sh"

TITLE="CommanderOS Restore Menu"

pause() {
    read -rp "Press ENTER to continue..."
}

# -------------------------------------------------------------------
# 1. Load backup archives
# -------------------------------------------------------------------
choose_backup() {
    echo "=== Available Backups ==="
    echo

    mapfile -t ARCHIVES < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" | sort -r)

    if [ ${#ARCHIVES[@]} -eq 0 ]; then
        echo "No backup archives found in $BACKUP_DIR."
        echo
        sleep 1
        return 1
    fi

    local i=1
    for a in "${ARCHIVES[@]}"; do
        echo "$i) $(basename "$a")"
        ((i++))
    done

    echo
    read -rp "Select a backup number to restore → " CHOICE

    if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || (( CHOICE < 1 || CHOICE > ${#ARCHIVES[@]} )); then
        echo "Invalid choice."
        return 1
    fi

    SELECTED_ARCHIVE="${ARCHIVES[CHOICE-1]}"
    echo "Selected: $(basename "$SELECTED_ARCHIVE")"
    return 0
}

# -------------------------------------------------------------------
# 2. Run secrets decryption (optional)
# -------------------------------------------------------------------
decrypt_secrets() {
    if [ ! -f "$DECRYPT_SCRIPT" ]; then
        echo "[WARN] No decrypt_secrets.sh script found. Skipping."
        return
    fi

    read -rp "Decrypt secrets? (y/N): " ANSWER
    if [[ "$ANSWER" =~ ^[Yy] ]]; then
        echo "[INFO] Decrypting secrets..."
        bash "$DECRYPT_SCRIPT" || echo "[ERROR] Decryption failed."
    else
        echo "[INFO] Skipping secrets decryption."
    fi
}

# -------------------------------------------------------------------
# 3. Restore backup contents
# -------------------------------------------------------------------
restore_backup() {
    echo "[INFO] Extracting backup: $SELECTED_ARCHIVE"
    tar -xzf "$SELECTED_ARCHIVE" -C "$HOME" || {
        echo "[ERROR] Extraction failed."
        exit 1
    }

    echo "[INFO] Running restore.sh..."
    bash "$RESTORE_SCRIPT"
}

# -------------------------------------------------------------------
# 4. Full system rebuild (optional)
# -------------------------------------------------------------------
full_rebuild() {
    if [ ! -f "$REBUILD_SCRIPT" ]; then
        echo "[WARN] No rebuild script found. Skipping."
        return
    fi

    read -rp "Do full CommanderOS rebuild? (y/N): " ANSWER
    if [[ "$ANSWER" =~ ^[Yy] ]]; then
        sudo bash "$REBUILD_SCRIPT"
    else
        echo "[INFO] Skipping full rebuild."
    fi
}

# -------------------------------------------------------------------
# MAIN MENU LOOP
# -------------------------------------------------------------------
while true; do
    clear
    echo "=============================="
    echo "  CommanderOS Restore Menu"
    echo "=============================="
    echo
    echo "1) Restore from backup archive"
    echo "2) Decrypt secrets only"
    echo "3) Run full system rebuild"
    echo "4) Exit"
    echo
    read -rp "Select an option → " OPT

    case "$OPT" in
        1)
            if choose_backup; then
                decrypt_secrets
                restore_backup
                full_rebuild
                pause
            fi
            ;;
        2)
            decrypt_secrets
            pause
            ;;
        3)
            full_rebuild
            pause
            ;;
        4)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid selection."
            sleep 1
            ;;
    esac
done

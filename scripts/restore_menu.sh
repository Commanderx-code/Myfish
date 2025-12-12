#!/usr/bin/env bash
set -euo pipefail

REPO="$HOME/MyFish"
BACKUP_DIR="$REPO/backups"
RESTORE_SCRIPT="$REPO/scripts/restore.sh"
REBUILD_SCRIPT="/usr/local/bin/myfish-rebuild.sh"
DECRYPT_SCRIPT="$REPO/scripts/secrets_decrypt.sh"
DIFF_SCRIPT="$REPO/scripts/diff_report.sh"
LOG="$REPO/restore_menu.log"

logo() {
    clear
    cat <<'EOF'
   ____                                     _ _           
  / ___|___  _ __ ___  _ __ ___   ___ _ __ (_) | ___ _ __ 
 | |   / _ \| '_ ` _ \| '_ ` _ \ / _ \ '_ \| | |/ _ \ '__|
 | |__| (_) | | | | | | | | | | |  __/ | | | | |  __/ |   
  \____\___/|_| |_| |_|_| |_| |_|\___|_| |_|_|_|\___|_|   

                CommanderOS Restore Menu
EOF
    echo
}

pause() {
    read -rp "Press ENTER to continue..."
}

choose_backup() {
    echo "=== Available Backups ==="
    echo

    mapfile -t ARCHIVES < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.tar.gz" 2>/dev/null | sort -r)

    if [ ${#ARCHIVES[@]} -eq 0 ]; then
        echo "No backup archives found in $BACKUP_DIR."
        echo
        sleep 1
        return 1
    fi

    local i=1
    for a in "${ARCHIVES[@]}"; do
        printf "%2d) %s\n" "$i" "$(basename "$a")"
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
    echo
    return 0
}

decrypt_secrets() {
    if [ ! -x "$DECRYPT_SCRIPT" ]; then
        echo "[WARN] No secrets_decrypt.sh script found. Skipping."
        return
    fi

    read -rp "Decrypt secrets before restore? (y/N): " ANSWER
    if [[ "$ANSWER" =~ ^[Yy] ]]; then
        echo "[INFO] Decrypting secrets..."
        bash "$DECRYPT_SCRIPT" | tee -a "$LOG" || echo "[ERROR] Decryption failed."
    else
        echo "[INFO] Skipping secrets decryption."
    fi
}

restore_backup() {
    if [ -z "${SELECTED_ARCHIVE:-}" ]; then
        echo "[ERROR] No archive selected."
        return 1
    fi

    echo "[INFO] Extracting backup: $SELECTED_ARCHIVE" | tee -a "$LOG"
    tar -xzf "$SELECTED_ARCHIVE" -C "$HOME" 2>>"$LOG"

    if [ -x "$RESTORE_SCRIPT" ]; then
        echo "[INFO] Running restore.sh..." | tee -a "$LOG"
        bash "$RESTORE_SCRIPT" | tee -a "$LOG"
    else
        echo "[WARN] $RESTORE_SCRIPT not found or not executable."
    fi
}

full_rebuild() {
    if [ ! -x "$REBUILD_SCRIPT" ]; then
        echo "[WARN] No myfish-rebuild.sh found. Skipping."
        return
    fi

    read -rp "Run full CommanderOS rebuild? (y/N): " ANSWER
    if [[ "$ANSWER" =~ ^[Yy] ]]; then
        echo "[INFO] Running full rebuild..." | tee -a "$LOG"
        sudo bash "$REBUILD_SCRIPT" | tee -a "$LOG"
    else
        echo "[INFO] Skipping full rebuild."
    fi
}

run_diff_report() {
    if [ ! -x "$DIFF_SCRIPT" ]; then
        echo "[WARN] No diff_report.sh found at $DIFF_SCRIPT."
        return
    fi

    echo "[INFO] Generating diff report..." | tee -a "$LOG"
    bash "$DIFF_SCRIPT" | tee -a "$LOG"
}

while true; do
    logo
    echo "1) Restore from backup archive"
    echo "2) Decrypt secrets only"
    echo "3) Run full system rebuild"
    echo "4) Generate diff report"
    echo "5) Exit"
    echo
    read -rp "Select an option → " OPT

    case "$OPT" in
        1)
            if choose_backup; then
                decrypt_secrets
                restore_backup
                full_rebuild
                run_diff_report
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
            run_diff_report
            pause
            ;;
        5)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid selection."
            sleep 1
            ;;
    esac
done


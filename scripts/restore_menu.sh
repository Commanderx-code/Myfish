#!/usr/bin/env bash
set -euo pipefail

MYFISH_DIR="$HOME/MyFish"
BACKUP_DIR="$MYFISH_DIR/backups"
LOG="$MYFISH_DIR/restore.log"

mkdir -p "$BACKUP_DIR"
touch "$LOG"

log() {
    echo "[$(date '+%F %T')] $*" | tee -a "$LOG"
}

pause() {
    read -rp "Press Enter to continue..."
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "❌ Required command not found: $1"
        exit 1
    }
}

banner() {
cat <<'EOF'


   ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ ███████╗██████╗
  ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝██╔══██╗
  ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
  ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
  ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████╗██║  ██║
   ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝

                    Commander Restore Environment
EOF
}

restore_backup() {
    require_cmd tar

    cd "$BACKUP_DIR" || {
        echo "❌ Backup directory not found"
        return
    }

    if ! ls *.tar.gz >/dev/null 2>&1; then
        echo "❌ No backups found in $BACKUP_DIR"
        return
    fi

    if command -v fzf >/dev/null 2>&1; then
        SELECTED_ARCHIVE=$(ls *.tar.gz | fzf --prompt="Select backup > ")
    else
        echo "Available backups:"
        select f in *.tar.gz; do
            SELECTED_ARCHIVE="$f"
            break
        done
    fi

    [ -z "${SELECTED_ARCHIVE:-}" ] && {
        echo "❌ No backup selected"
        return
    }

    echo
    echo "📦 Preview of backup contents:"
    tar -tzf "$SELECTED_ARCHIVE" | head -n 20
    echo "..."

    read -rp "⚠️  Restore this backup to your HOME directory? (y/N): " CONFIRM
    [[ "$CONFIRM" != "y" ]] && return

    log "Restoring backup: $SELECTED_ARCHIVE"
    tar -xzf "$SELECTED_ARCHIVE" -C "$HOME"
    log "Restore completed"
    echo "✅ Restore completed successfully"
}

decrypt_secrets() {
    SCRIPT="$MYFISH_DIR/scripts/decrypt_secrets.sh"

    if [ ! -x "$SCRIPT" ]; then
        echo "❌ decrypt_secrets.sh not found or not executable"
        return
    fi

    log "Decrypting secrets"
    sudo "$SCRIPT"
    log "Secrets decrypted"
}

full_rebuild() {
    SCRIPT="$MYFISH_DIR/scripts/rebuild.sh"

    if [ ! -x "$SCRIPT" ]; then
        echo "❌ rebuild.sh not found or not executable"
        return
    fi

    read -rp "⚠️  Run FULL system rebuild? (y/N): " CONFIRM
    [[ "$CONFIRM" != "y" ]] && return

    log "Starting full rebuild"
    sudo "$SCRIPT"
    log "Full rebuild finished"
}

while true; do
    clear
    banner
    echo
    echo "1) Restore from backup archive"
    echo "2) Decrypt secrets only"
    echo "3) Run full system rebuild"
    echo "4) Exit"
    echo
    read -rp "Select option: " CHOICE

    case "$CHOICE" in
        1) restore_backup; pause ;;
        2) decrypt_secrets; pause ;;
        3) full_rebuild; pause ;;
        4) exit 0 ;;
        *) echo "Invalid option"; pause ;;
    esac
done


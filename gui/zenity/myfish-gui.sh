#!/usr/bin/env bash

ACTION=$(zenity --list \
  --title="CommanderOS • MyFish" \
  --width=420 \
  --height=300 \
  --column="Action" \
  "Restore MyFish Configs" \
  "Decrypt Secrets" \
  "Rebuild System" \
  "Run Autosync" \
  "Exit")

case "$ACTION" in
  "Restore MyFish Configs")
    gnome-terminal -- bash -c "~/MyFish/scripts/restore.sh; exec bash"
    ;;
  "Decrypt Secrets")
    gnome-terminal -- bash -c "~/MyFish/scripts/decrypt_secrets.sh; exec bash"
    ;;
  "Rebuild System")
    gnome-terminal -- bash -c "~/MyFish/scripts/rebuild.sh; exec bash"
    ;;
  "Run Autosync")
    gnome-terminal -- bash -c "~/MyFish/autosync.sh; exec bash"
    ;;
  *)
    exit 0
    ;;
esac


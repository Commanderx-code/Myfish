#!/usr/bin/env bash
cd ~/MyFish
git pull --rebase
git add -A
git commit -m "Auto-sync $(date '+%Y-%m-%d %H:%M:%S')" || true
git push

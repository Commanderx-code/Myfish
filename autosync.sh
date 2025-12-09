#!/usr/bin/env bash
cd ~/MyFish || exit
git add .
git commit -m "Auto-sync $(date '+%Y-%m-%d %H:%M')" || exit 0
git push

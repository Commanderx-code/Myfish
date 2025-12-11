#!/usr/bin/env bash
set -e

REPO="$HOME/MyFish"
REPORT="$REPO/diff_report_$(date '+%Y-%m-%d_%H-%M-%S').txt"

echo "MyFish Diff Report - $(date)" | tee "$REPORT"
echo "====================================" | tee -a "$REPORT"

echo -e "\n[1] APT package diff" | tee -a "$REPORT"
if [ -f "$REPO/pkgs/packages.txt" ]; then
    comm -3 <(sort "$REPO/pkgs/packages.txt") <(dpkg --get-selections | awk '{print $1}' | sort) | tee -a "$REPORT"
else
    echo "  packages.txt not found" | tee -a "$REPORT"
fi

if command -v brew >/dev/null 2>&1 && [ -f "$REPO/pkgs/brew_packages.txt" ]; then
    echo -e "\n[2] Brew package diff" | tee -a "$REPORT"
    comm -3 <(sort "$REPO/pkgs/brew_packages.txt") <(brew leaves | sort) | tee -a "$REPORT"
fi

if command -v flatpak >/dev/null 2>&1 && [ -f "$REPO/pkgs/flatpaks.txt" ]; then
    echo -e "\n[3] Flatpak app diff" | tee -a "$REPORT"
    comm -3 <(sort "$REPO/pkgs/flatpaks.txt") <(flatpak list --app --columns=application | sort) | tee -a "$REPORT"
fi

echo -e "\n[4] Config dir diffs (fish, ranger, fastfetch)" | tee -a "$REPORT"
diff -rq ~/.config/fish "$REPO/configs/fish" 2>/dev/null | tee -a "$REPORT" || true
diff -rq ~/.config/ranger "$REPO/configs/ranger" 2>/dev/null | tee -a "$REPORT" || true
diff -rq ~/.config/fastfetch "$REPO/configs/fastfetch" 2>/dev/null | tee -a "$REPORT" || true

echo -e "\n[5] Themes/icons/fonts diffs" | tee -a "$REPORT"
diff -rq ~/.themes "$REPO/configs/themes" 2>/dev/null | tee -a "$REPORT" || true
diff -rq ~/.icons "$REPO/configs/icons" 2>/dev/null | tee -a "$REPORT" || true
diff -rq ~/.local/share/fonts "$REPO/configs/fonts" 2>/dev/null | tee -a "$REPORT" || true

echo -e "\n[✓] Diff report written to: $REPORT"

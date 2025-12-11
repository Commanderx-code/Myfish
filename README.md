# CommanderOS – MyFish Environment & Restore Framework

CommanderOS is my personal Linux environment built on top of Zorin / Ubuntu,
managed through this `MyFish` repo.

It gives me:

- 🔁 **Full environment restore** on any machine
- 🌈 **Custom shell + terminal setup** (fish, starship, fastfetch, themes)
- 📦 **Package restore** (APT/Nala, Flatpak, Homebrew)
- 💾 **Automated backups** with pruning + dedicated Git branch
- 🧪 **Custom CommanderOS ISO** that can auto-restore this environment on first boot

This repo is both my **dotfiles** and my **“mini config management system”**.

---

## 🔧 Repo Layout

```text
MyFish/
  configs/
    fish/            # config.fish, conf.d, functions, completions
    fastfetch/       # fastfetch config + logo
    ranger/          # ranger config
    starship.toml    # starship prompt config
    themes/          # GTK/icon/cursor theme files
    icons/           # extra icon themes
    fonts/           # nerd fonts & other custom fonts

  pkgs/
    packages.txt         # APT/Nala package list
    brew_packages.txt    # Homebrew packages
    flatpaks.txt         # Flatpak apps

  secrets/
    encrypted/           # (optional) .gpg files
    plain/               # decrypted secrets (git-ignored)

  systemd/
    user/                # user-level systemd units (autosync, etc.)

  scripts/
    backup.sh            # backup configs + package lists + archives
    restore.sh           # restore configs + packages
    rebuild.sh           # full CommanderOS rebuild on a new system
    diff_report.sh       # compare live system vs repo
    sync.sh              # run backup + git sync
    secrets_encrypt.sh   # (optional) encrypt sensitive files
    secrets_decrypt.sh   # (optional) decrypt sensitive files

  backups/               # .tar.gz archives of configs + packages
  autosync.log           # log from sync/autobackup (in .gitignore)
  README.md
  .gitignore

# MyFish – Personal Linux Environment & Backup

This repo stores my entire terminal/Linux environment in a reproducible, portable way.

- Shell: **fish** + **starship**
- Terminal goodies: **ranger**, **fastfetch**, **eza**, etc.
- Package managers: **APT/Nala**, **Homebrew**, **Flatpak**
- Secrets: **WiFi + SSH**, encrypted with GPG
- Automation: **systemd user timer** for auto Git sync

---

## Layout

```text
MyFish/
  configs/       # dotfiles and visual stuff
    fish/        # fish config, functions, conf.d, completions
    fastfetch/   # fastfetch config + logo
    ranger/      # ranger config
    starship.toml
    themes/
    icons/
    fonts/
  pkgs/          # package lists
    packages.txt
    brew_packages.txt
    flatpaks.txt
  secrets/
    encrypted/   # *.gpg files (committed)
    plain/       # decrypted secrets (ignored by git)
  systemd/
    user/
      autosync.service
      autosync.timer
  scripts/
    backup.sh
    restore.sh
    rebuild.sh
    diff_report.sh
    sync.sh
    secrets_encrypt.sh
    secrets_decrypt.sh

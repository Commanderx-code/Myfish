# Commander-os

A Linux terminal environment with a guided installer. Choose **Home Manager** or
**direct installation**, then choose **Fish, Bash, Zsh, or keep your current shell**.
This is a starter project, not an operating system image.

## Install

```sh
git clone https://github.com/Commanderx-code/Commander-os.git
cd Commander-os
./install.sh --apply
```

Without Git, download and extract **Code → Download ZIP** on GitHub, then run
`bash install.sh --apply` from the extracted folder. Run as your normal user,
without sudo; the installer requests elevated access only where needed.

The installer asks which installation mode and shell you want before installing
prerequisites. A new configuration defaults to Fish; existing settings are reused
unless you select another shell. It shows a plan and asks for `APPLY` before
activating or writing your shell configuration. Log out and back in after
accepting a login-shell change. Terminal profiles set to run Bash explicitly
must be changed to use the account's default shell.

| Mode | Installation and updates | Configuration recovery |
| --- | --- | --- |
| Home Manager | Installs Nix if needed; pinned packages from `flake.lock` | Home Manager generations and backups of conflicting files |
| Direct | Uses apt, dnf, or pacman; Starship's official installer if needed | Timestamped copies of changed configuration files |

Both modes provide CLI tools, Starship, zoxide, fzf and optional Neovim. Shell
configuration follows your selected shell. Direct development mode installs Git;
Lazygit is currently included only in Home Manager development mode. Direct mode
preserves any existing Neovim configuration. Package versions follow the distro
in direct mode. Home Manager keeps all three supported shell executables installed
so declining a subsequent shell change does not remove your existing login shell.

Direct mode never installs Nix or Home Manager. It refuses an existing Home
Manager profile or symlink-managed target configuration; test it in a separate
account or VM instead of mixing managers. Keeping the current shell skips shell
configuration and login-shell changes; it still installs selected tools. Neither
mode configures your desktop, bootloader or backup services.

## Settings and previews

Settings live outside Git at `~/.config/commander-os/machine.json` (respecting
`XDG_CONFIG_HOME`). The `shell` field accepts `fish`, `bash`, `zsh`, or `keep`.
`features.neovim` and `features.development` control optional tools. Older settings
using `features.fish` remain supported; an explicit `shell` takes precedence.

```sh
# Create settings without a Home Manager build:
./install.sh --init --backend home-manager --shell fish

# Build a Home Manager preview:
./install.sh --backend home-manager --shell bash

# Show the direct-install plan without installing its tools or writing shell files:
./install.sh --backend native --shell zsh

# Apply direct mode:
./install.sh --apply --backend native --shell fish
```

Missing Python may be installed after confirmation, even for a preview. Use
`--no-install` to prohibit dependency installation. Explicit `--backend` selects
a mode without a menu; `--shell` selects and saves a shell choice. Unknown command
arguments fail before dependency installation.

Home Manager mode uses an explicit source-file allowlist and supplies validated
machine settings in a temporary build tree. You do not need to track personal
settings in Git. Nix stores usernames and home paths in its normally readable
store: never put secrets in Nix settings. Preserve `home.stateVersion` on updates.

## System prerequisites

The bootstrap supports apt, dnf and pacman. Automatic Nix installation uses the
[official Nix installer](https://nixos.org/download/) and requires systemd Linux
with SELinux disabled. Existing incomplete Nix installations stop with guidance.
Direct mode does not have that Nix requirement. On Arch, package installation uses
the existing package database; do your normal full system update if it is stale.

Direct mode uses the [official Starship installer](https://starship.rs/guide/)
for a missing Starship executable and places it in `~/.local/bin`. Downloads and
package installation happen only after the displayed installation plan is accepted.

## Updates and recovery

```sh
git pull --ff-only
./install.sh --apply
```

Before replacing an existing Home Manager configuration, record
`home-manager generations` and keep its configuration checkout. Run a previous
generation's `/nix/store/…-home-manager-generation/activate` to roll back, then
restore unmanaged files from `.commander-os-…` backups as needed. On a first
installation, `home-manager uninstall` can remove the managed home environment.
See the [Home Manager manual](https://nix-community.github.io/home-manager/).

Before removing a Home Manager shell, restore your login shell using
`chsh -s /bin/bash` or the previous path recorded at
`~/.local/state/commander-os/previous-shell.txt` (respecting `XDG_STATE_HOME`).
Generation rollback does not undo `chsh` or `/etc/shells` registration. Do not
remove the profile your login shell points to before changing it back.

Direct mode backs up changed files as `FILE.commander-os-TIMESTAMP`, preserves
existing Bash/Zsh startup contents, and avoids duplicate startup entries on
repeat runs. To undo it, first restore the previous login shell. Restore desired
backup files and remove the Commander-os startup block from `.bashrc` or `.zshrc`,
or remove `~/.config/fish/conf.d/commander-os.fish`. Remove Commander-os's shell
snippets under `~/.config/commander-os/` if no longer needed. Tools installed by
your package manager remain installed; there is no automatic native uninstaller.

## Validation and scope

```sh
nix develop --command python3 -B -m unittest discover -s tests -v
nix develop --command shellcheck install.sh scripts/prerequisites.sh
nix flake check
```

Targets: x86_64 and aarch64 Linux. Builds are tested on x86_64; clean-machine,
ARM, and cross-distro activation testing remains in progress. macOS is unsupported.
The setup flow is inspired by [ChrisTitusTech/mybash](https://github.com/ChrisTitusTech/mybash),
with independently implemented installers and selectable shells. Fuller visual
themes, Nerd Font setup and desktop integration remain future work.

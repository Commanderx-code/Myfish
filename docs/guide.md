# Myfish · setup and reference

[← Back to Myfish](../README.md)

A Linux and macOS terminal environment with a guided installer. Choose **Home Manager** or
**direct installation**, then choose **Fish, Bash, Zsh, or keep your current shell**.
This is a starter project, not an operating system image.

Formerly **Commander-os**. Existing settings directories, startup markers,
environment variables and recovery records keep their original names so installed
setups continue to update and uninstall correctly. Existing checkout folders can
keep their current name; new clones use `Myfish`.

## Install

```sh
git clone https://github.com/Commanderx-code/Myfish.git
cd Myfish
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
| Direct | Uses apt, dnf, pacman, or macOS Homebrew; Starship included | Timestamped copies of changed configuration files |

Both modes provide CLI tools, a Powerline-style Starship theme, zoxide, fzf and optional Neovim.
Home Manager also installs JetBrainsMono Nerd Font (fontconfig on Linux,
`~/Library/Fonts/Commander-os` on macOS). Select
**JetBrainsMono Nerd Font** in your terminal preferences to render the separators
and icons. Direct mode installs the Nerd Font through Homebrew on macOS or a checksum-verified
upstream download on Linux. Linux installs the four Mono styles and their license
in `$XDG_DATA_HOME/fonts/commander-os` (default `~/.local/share/fonts/commander-os`),
refreshes fontconfig, and records those files for removal. Existing registered
JetBrainsMono Nerd Font Mono installations are reused. Shell
configuration follows your selected shell. Direct development mode installs Git;
Lazygit is included in Home Manager and macOS direct development mode. Direct mode
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

The bootstrap supports apt, dnf and pacman on Linux, and Homebrew on macOS. Automatic Nix installation uses the
[official Nix installer](https://nixos.org/download/) and supports macOS or systemd Linux
with SELinux disabled. Existing incomplete Nix installations stop with guidance.
Direct mode does not have that Nix requirement. On Arch, package installation uses
the existing package database; do your normal full system update if it is stale.

Linux direct mode uses the [official Starship installer](https://starship.rs/guide/)
for a missing Starship executable and places it in `~/.local/bin`. Downloads and
package installation happen only after the displayed installation plan is accepted.

### macOS

Run the same installer as your normal account. On **macOS only**, it checks for
Homebrew (including `/opt/homebrew` on Apple Silicon and `/usr/local` on Intel).
If missing, it offers the [official Homebrew installer](https://docs.brew.sh/Installation),
which may request administrator access and Xcode Command Line Tools. Existing
Homebrew installations are reused. `--no-install` never bootstraps Homebrew.
Both installation modes use this check; Home Manager additionally needs Nix.

Direct mode uses Homebrew for packages, Starship and JetBrainsMono Nerd Font.
Bash uses current Homebrew Bash, and Zsh includes autosuggestions and syntax
highlighting. Startup files restore Homebrew paths in new terminals. Choose
**JetBrainsMono Nerd Font** in Terminal/iTerm preferences after installation.
Use a macOS version supported by Homebrew; Windows is not supported.

Uninstall/reinstall works through `./uninstall.sh`. Native package removal only
offers packages recorded as newly installed by Commander-os. It leaves Homebrew,
Nix, existing packages and recovery backups in place. Home Manager detachment
keeps its Nix tools; it does not convert them into Homebrew packages.

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
your package manager can be reviewed with the maintenance menu below.

## Validation and scope

```sh
nix develop --command python3 -B -m unittest discover -s tests -v
nix develop --command shellcheck uninstall.sh install.sh scripts/prerequisites.sh
nix flake check
```

Targets: x86_64 and aarch64 Linux, plus Intel and Apple Silicon macOS.
CI checks Linux x86_64 and both Mac architectures without activating a home.
Clean-machine installation, graphical terminal behavior, Linux ARM and
cross-distro activation still need manual testing. Intel Home Manager support
is limited by the pinned Nixpkgs release; future Nixpkgs updates may drop it.
The setup flow is inspired by [ChrisTitusTech/mybash](https://github.com/ChrisTitusTech/mybash),
with independently implemented installers and selectable shells. Automatic terminal font selection and desktop
integration remain future work.

## Prompt status

The prompt shows a green `λ` after success or a red `×` after an unsuccessful
command. It does not display exit-code labels or pipeline details. A search
finding no matches can return a nonzero status without indicating a broken
installation. The indicator follows the final status supplied by the shell.
The clock and package icons use the installed Nerd Font rather than emoji
fallback fonts.

## Greeting

The installer offers a custom greeting, no greeting, or the saved/default choice.
This works for Fish, Bash and Zsh with either backend. `{user}` inserts the
account username; all other text is printed literally, never executed as shell code.
The default is `Hello, {user} ⚡`. Turning off the greeting keeps Fastfetch enabled.

```sh
./install.sh --apply --greeting 'Welcome back, {user}!'
./install.sh --apply --no-greeting
./install.sh --apply --default-greeting
```

The choice is saved as `greeting` in your machine settings and survives reinstalls.
An empty string disables it. `COMMANDER_QUIET=1` still suppresses both the greeting
and Fastfetch for an individual shell session.

## Fish customizations

Fish now includes the portable customizations from the personal dotfiles:

- Colored, icon-based `ls`, `ll`, `la`, `tree`, sort/filter variants and Git status listings.
- `..`, `...`, `bd`, and `home` navigation abbreviations; `mkcd`, `fcd`/`cdi`, `dirsize`, and `psg`.
- Ctrl-P file picker, Ctrl-F text search, Ctrl-H fuzzy history, and `**` followed by Tab for file completion. Ctrl-R remains available.
- File, image and PDF previews; Ctrl-/ toggles the preview pane. Image previews depend on terminal sixel support.
- `gcom` stages and commits; `lazyg` additionally pushes, stopping on errors.
- `extract`, broot's `br` launcher, and `serve` (localhost only, port 8000 by default).
- Syntax colors, a username-based greeting, Fastfetch when installed, and long-command notifications.

`rm` uses the trash when `trash-cli` is installed; `cp` and `mv` ask before overwriting.
Use `command rm`, `command cp`, or `command mv` for the underlying utilities.
Set `COMMANDER_QUIET=1` before launching Fish to suppress the greeting and Fastfetch.
The notification plugin retains its MIT license in `modules/fish/conf.d/80-done.fish`.

Home Manager installs the preview, archive, notification, Fastfetch and broot dependencies.
Direct mode installs Fastfetch and the basic Fish helper dependencies. macOS
also installs broot, PDF and 7z tools and uses system notifications. On Linux,
those extra helpers require their corresponding distro packages.
Personal Config Bible/backup commands, SSH-agent startup, music-player autostart,
and Arch-only maintenance shortcuts have not been imported into this portable setup.

Both installation modes use the [Chris Titus Tech Fastfetch layout](https://github.com/ChrisTitusTech/mybash/blob/main/config.jsonc)
at `~/.config/fastfetch/config.jsonc` (respecting `XDG_CONFIG_HOME` in native mode).
It includes grouped OS, desktop, hardware and audio information. The bundled
configuration retains its MIT license. Existing configurations use the normal
backup/recovery flow; selecting “keep current shell” leaves Fastfetch configuration alone.

Native Fish, Bash and Zsh installs include Fastfetch when it is missing. On apt
systems, the installer prefers the distro package after refreshing package lists.
If no candidate exists, it downloads the official Fastfetch 2.68.1 `.deb` for amd64
or arm64 and checks the release SHA-256 before installing it through apt. This
fallback is announced before confirmation and recorded for later removal. See
[Fastfetch's release](https://github.com/fastfetch-cli/fastfetch/releases/tag/2.68.1).
Existing Fastfetch installations are reused; `--no-install` refuses missing tools.

## Bash and Zsh customizations

Bash and Zsh now share the Fish-style `eza` aliases, directory shortcuts, `mkcd`,
`fcd`/`cdi`, `fdi`, `rgi`, Git helpers, archive extraction, broot launcher, localhost
web server, greeting and Fastfetch. The common implementation lives in
`modules/shell/common.sh`; each shell has its own key-binding adapter. Both
Home Manager and direct mode install these files when that shell is selected.

| Feature | Bash | Zsh | Fish |
| --- | --- | --- | --- |
| File / text picker | Ctrl-P / Ctrl-F | Ctrl-P / Ctrl-F | Ctrl-P / Ctrl-F |
| History | fzf Ctrl-R; Ctrl-H when its widget exists | fzf Ctrl-R; Ctrl-H when its widget exists | Ctrl-R / Ctrl-H |
| Directory shortcuts | aliases | aliases | abbreviations |
| Syntax / suggestions | ble.sh highlighting and autosuggestions (both installers) | Home Manager and macOS native enable highlighting and autosuggestions | built in, with custom colors |
| Notifications | `notify-run COMMAND` | `notify-run COMMAND` | automatic long-command notifications |

Starship, fzf and zoxide remain initialized through each shell's integration.
Bash/Zsh preserve normal Tab behavior and use fzf's available completion support.
Text-search pickers currently expect filenames without colons; file/directory
pickers preserve spaces. `notify-run` preserves the command's exit status and
uses `notify-send` on Linux or the system notification service on macOS. Direct mode requires optional
broot/preview packages just as the Fish setup does; automatic Zsh
highlighting and suggestions are provided by Home Manager and macOS native mode.

Bash loads ble.sh before Starship and attaches it after startup. Press **Right Arrow**
to accept a suggestion; **Ctrl-F** stays assigned to the text picker. Suggestions
learn from your command history. Set `export COMMANDER_BLE=0` before the Commander-os
startup entry to disable it. It only loads in interactive terminals.
Home Manager uses the pinned Nix package. Direct mode builds upstream ble.sh into
`~/.local/share/blesh`, installing Git, make and gawk if missing; reruns reuse it.

Home Manager Zsh suggests from its own history, then falls back to completion.
Fish and Bash history are not imported. Suggestions use gray text; press Right
Arrow at the end of the command to accept one.

To select Bash or Zsh:

```sh
./install.sh --apply --backend home-manager --shell bash
# Or choose --shell zsh. For a clean direct-mode account, use --backend native.
```

Accept the login-shell prompt, then log out and back in. Pulling repository updates does not activate a new configuration; rerun the installer
to apply them to the current account.


## Uninstall and reinstall

Run `./uninstall.sh` for a prompted menu:

1. Uninstall all Myfish components.
2. Reinstall your saved setup.
3. Choose components to remove: shell customizations, Neovim, or development tools.
4. Choose components to reinstall.
5. Remove Home Manager while keeping your current tools and configuration.
6. Show installation status.

Run as your normal user. Each removal shows a plan, makes a recovery backup, and
asks for an exact confirmation. It changes the login shell to a registered system
shell before removing anything that could supply the current login shell.

Explicit command-line actions default to a preview. Add `--apply` to build and
confirm changes in an interactive terminal:

```sh
./uninstall.sh --action status
./uninstall.sh --action remove
./uninstall.sh --action remove --components neovim --apply
./uninstall.sh --action reinstall --apply
./uninstall.sh --action detach --apply
```

Use `--config PATH` for a custom machine settings file. Multiple components use
commas, for example `--components neovim,development`. Reinstall reapplies the
saved configuration and ensures tools are installed; it does not clear history
or force-download working packages. Reinstalling selected features enables those
features. Home Manager component changes rebuild the whole generation while
keeping the other saved feature choices.

**Remove Home Manager, keep my setup:** the script preserves the current packages,
fonts and plugins in a separate Nix environment and turns managed configuration
into editable files. It omits the Home Manager command from the new environment.
Nix stays installed: these tools and configuration still use its store. This is a
fixed snapshot, not a migration to apt, dnf or pacman; Home Manager will no longer
update it. To switch back to an installer, choose reinstall. The script asks to
remove the detached snapshot first and backs up your files. Detached packages are
one environment, so selecting individual components requires returning to an
installer. Unrelated Nix profile entries are preserved.

**Uninstall all** covers Myfish for this account. Home Manager's upstream
uninstall module removes its entire active generation and generation history.
The script requires a recorded or recognizable Commander-os generation, pins a
recovery generation first, and restores earlier timestamped Commander-os file
backups where available. It refuses an unrecognized Home Manager setup.

Direct installations now record original configuration and which requested
distro packages were absent before installation. Removal restores originals or
removes unchanged installed files. Edited files are kept; unchanged Commander-os
startup entries can be removed without discarding other Bash/Zsh startup content.
You can choose which recorded packages to remove and review the package manager's
transaction. It does not automatically remove dependencies. System Bash and the
recovery shell are retained. Selective Neovim removal can remove recorded Neovim;
shared distro tools are offered through full removal.

Older direct installs lack ownership records. Matching Commander-os configuration
can be removed, but unknown packages, existing Neovim configuration and old backup
files are preserved. Reapplying an older direct install cannot reconstruct which
packages were originally present.

Nix itself, shared installation prerequisites, personal files, shell history,
saved machine settings and recovery backups remain. Private installation records
and backups live in `${XDG_STATE_HOME:-$HOME/.local/state}/commander-os`.
Recovery roots intentionally prevent garbage collection from deleting saved
Nix packages. If an operation stops midway, it prints the backup path and the
saved `generation/activate` recovery command. After restoring, run the installer
again to refresh the installation record. No removal is run against the runner's
active account during automated checks; a complete desktop/logout cycle still
needs testing in a disposable VM.

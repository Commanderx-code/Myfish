<p align="center">
  <img src="docs/assets/banner.svg" alt="Myfish — Your shell. Your setup. Fish, Bash and Zsh for Linux and macOS." width="960">
</p>

<p align="center">
  <a href="https://github.com/Commanderx-code/Myfish/actions/workflows/check.yml"><img src="https://github.com/Commanderx-code/Myfish/actions/workflows/check.yml/badge.svg" alt="Validation status"></a>
  <img src="https://img.shields.io/badge/shells-Fish%20%C2%B7%20Bash%20%C2%B7%20Zsh-86bbd8?style=flat-square" alt="Fish, Bash and Zsh">
  <img src="https://img.shields.io/badge/platforms-Linux%20%C2%B7%20macOS-5eead4?style=flat-square" alt="Linux and macOS">
  <img src="https://img.shields.io/badge/Home_Manager-optional-5e81ac?style=flat-square" alt="Home Manager optional">
</p>

<p align="center">
  A personalized terminal, with a guided setup and a way back.<br>
  Choose your shell, choose how to manage it, and make yourself at home.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#what-you-get">Features</a> ·
  <a href="#make-it-yours">Customize</a> ·
  <a href="docs/guide.md">Full guide</a> ·
  <a href="https://github.com/Commanderx-code/Myfish/issues">Report an issue</a>
</p>

## What you get

Myfish brings a consistent terminal setup to **Fish, Bash and Zsh**. Use your system’s
package manager or opt into **Home Manager** for pinned packages and generations.

| | Included |
| :--- | :--- |
| **A recognizable prompt** | A shared Powerline-style Starship theme with directory, Git and clock segments. |
| **Icons that render** | JetBrainsMono Nerd Font installation and a grouped Fastfetch system overview. |
| **Faster navigation** | zoxide, fzf file and text pickers, eza listings and directory shortcuts. |
| **Persistent terminal sessions** | Zellij with Tokyo Night Storm, your selected shell and locked shortcuts; launch manually. |
| **A personal welcome** | Write your own greeting, insert your username, or turn the greeting off. |
| **Everyday helpers** | Git shortcuts, archive extraction and optional Neovim with the official LazyVim starter, plus development tools. |
| **Maintenance included** | Reinstall, remove selected components, or detach Home Manager while keeping your tools. |

Fish includes built-in suggestions and highlighting. Bash uses **ble.sh**. Zsh
suggestions and highlighting are configured through Home Manager or macOS native
installation. See the [shell comparison](docs/guide.md#bash-and-zsh-customizations)
for key bindings and backend differences.

## Quick start

```sh
git clone https://github.com/Commanderx-code/Myfish.git
cd Myfish
./install.sh --apply
```

The installer walks you through the installation mode, shell and greeting. It
shows the configuration plan and asks for `APPLY` before applying it. Run as your
normal user; it requests elevated access when needed for dependencies or login-shell changes.

**After installation:** select **JetBrainsMono Nerd Font Mono** in your terminal’s
font settings, then close all terminal windows and reopen them. If you changed
your login shell, log out and back in.

<details>
<summary><strong>No Git installed?</strong></summary>

Download **Code → Download ZIP** from this repository, extract it, and run
`bash install.sh --apply` from the extracted folder.

</details>

## Choose your setup

| Mode | Package management | Best suited to |
| :--- | :--- | :--- |
| **Native / direct** | apt, dnf, pacman or macOS Homebrew | A setup using your existing package manager, without Nix. |
| **Home Manager** | Nix packages pinned by `flake.lock` | A declarative home configuration with generation-based recovery. |

```sh
# Native Fish setup
./install.sh --apply --backend native --shell fish

# Home Manager with Zsh
./install.sh --apply --backend home-manager --shell zsh
```

Both modes support Fish, Bash and Zsh. You can also choose **keep current shell**
to install selected tools without replacing your shell configuration.

On **macOS only**, the installer checks for Homebrew and offers to install it if
missing. Home Manager mode additionally installs Nix when needed. Native mode
refuses an existing Home Manager profile or symlink-managed target configuration;
use the [maintenance menu](#update-or-uninstall) when changing how you manage a setup.

### Platform support

| Platform | Native package manager | Automated coverage |
| :--- | :--- | :--- |
| Debian / Ubuntu family | apt | Linux x86_64 CI on Ubuntu |
| Fedora family | dnf | Package-planning tests |
| Arch family | pacman | Package-planning tests |
| macOS — Apple Silicon & Intel | Homebrew | CI on both Mac architectures |

CI runs tests and Home Manager builds without activating a home. Clean-machine
installation, desktop behavior, Linux ARM and cross-distro activation still need
manual testing. Automatic Nix setup on Linux requires systemd with SELinux disabled;
macOS must meet Homebrew’s requirements. Intel Home Manager support depends on the
pinned Nixpkgs release. [Platform details →](docs/guide.md#system-prerequisites)

Myfish configures a terminal environment; it does not install an operating system
or configure your desktop, bootloader or backup services.

## Make it yours

### Pick a greeting

```sh
./install.sh --apply --greeting 'Welcome back, {user}!'
./install.sh --apply --no-greeting
./install.sh --apply --default-greeting
```

`{user}` inserts the account username. Custom text is printed literally. Disabling
the greeting keeps Fastfetch enabled; `COMMANDER_QUIET=1` suppresses both for a session.

### Keep your preferences

Your shell, greeting and optional features are saved outside the repository in
`~/.config/commander-os/machine.json`, respecting `XDG_CONFIG_HOME`.

- **Shell:** `fish`, `bash`, `zsh` or `keep`.
- **Editor:** toggle Neovim with the default LazyVim starter.
- **Development:** toggle Git configuration and the tools available for your backend.

To inspect a native installation plan first:

```sh
./install.sh --backend native --shell fish --no-install
```

`--no-install` prohibits dependency installation. Other preview commands may offer
to install prerequisites. [Settings and previews →](docs/guide.md#settings-and-previews)

## Neovim with LazyVim

Enabling Neovim installs the [official LazyVim starter](https://github.com/LazyVim/starter).
Open `nvim` after installation; its first launch downloads the plugins. Then run
`:LazyHealth` to check the setup. Internet access is required for that first launch.

Native installs upgrade Myfish's unchanged minimal editor config, while preserving
existing personal or edited configs. Home Manager manages the starter Lua files;
its generated plugin lockfile remains writable. Plugins update through lazy.nvim,
independently of Myfish's Nix lock.

Older native Linux packages get checksum-verified Neovim and Tree-sitter binaries
under `~/.local`, with install records for removal. macOS uses Homebrew; Home Manager
supplies the tools through Nix. [Editor details →](docs/guide.md#neovim-and-lazyvim)

## Update or uninstall

Update your saved setup:

```sh
git pull --ff-only
./install.sh --apply
```

Open the maintenance menu:

```sh
./uninstall.sh
```

Choose a full reinstall, remove selected components, inspect installation status,
or remove Home Manager while keeping its tools as a fixed Nix snapshot.

Removal previews the changes, creates a recovery backup and asks for confirmation.
Native removal restores original files where possible, preserves edited files and
offers only recorded packages for removal. Nix, Homebrew, personal history and
recovery backups remain. Home Manager removal covers its entire active generation
and generation history. [Maintenance and recovery details →](docs/guide.md#uninstall-and-reinstall)

## Documentation

| Guide | What it covers |
| :--- | :--- |
| [Setup and reference](docs/guide.md) | Prerequisites, installation choices and platform behavior. |
| [Shell customizations](docs/guide.md#fish-customizations) | Aliases, pickers, previews and everyday commands. |
| [Recovery and rollback](docs/guide.md#updates-and-recovery) | Backups, login-shell recovery and generations. |
| [Validation](docs/guide.md#validation-and-scope) | Local checks and the limits of automated testing. |

Found a problem? [Open an issue](https://github.com/Commanderx-code/Myfish/issues)
with your OS, shell, installation mode, command and relevant error output.
Remove personal information before sharing logs.

## Credits

Inspired by [Chris Titus Tech’s mybash](https://github.com/ChrisTitusTech/mybash),
with a guided installer and support for multiple shells. The bundled Fastfetch
layout retains its upstream MIT notice, and downloaded fonts include their license.

Built with [Starship](https://starship.rs/), [Nerd Fonts](https://www.nerdfonts.com/),
[Fastfetch](https://github.com/fastfetch-cli/fastfetch),
[Home Manager](https://github.com/nix-community/home-manager) and the shell tools
listed in the guide.

---

<sub>Previously Commander-os. Existing settings paths, startup markers and recovery
records keep their original names so existing installations remain compatible.</sub>

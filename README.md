# Commander-os

A portable Linux home environment built with Nix and Home Manager. This is an
initial starter, not an operating-system image or a distribution installer.

The default setup provides Fish, Starship, Neovim, fuzzy finding, directory
navigation, and common CLI tools. Git and Lazygit are optional. It does not change
your bootloader, desktop or backup services. With Fish enabled, activation offers to make Fish
your login shell. Prerequisites may be installed through your package manager.

## Get started

Run the guided installer as your normal user:

```sh
git clone https://github.com/Commanderx-code/Commander-os.git
cd Commander-os
./install.sh --apply
```

You can also download and extract this repository using GitHub's **Code →
Download ZIP** button if Git is not installed. Open a terminal in the extracted
folder and run `bash install.sh --apply`.

The script detects missing Python 3, Git, curl and xz, and offers to install them
using apt, dnf or pacman. It shows the package list and asks before using sudo.
On Arch, it uses the existing package database; if installation fails due to stale
mirrors, perform your normal full system update before retrying.

If Nix is missing, the script offers to download and run the
[official Nix installer](https://nixos.org/download/), then loads Nix into the
current process and continues. Automatic Nix installation supports systemd Linux
with SELinux disabled. Existing broken Nix installations and unsupported systems
stop with guidance instead of modifying the host. Home Manager needs no separate
installation: Nix builds it along with the selected tools.

Settings are created at `~/.config/commander-os/machine.json` (or under your
`XDG_CONFIG_HOME`). Defaults come from your current account. Edit `fish`, `neovim`
and `development` to select features. Use `./install.sh --init` to create settings
before building. Never run the whole script with sudo.

To prepare dependencies and build without activation, run `./install.sh`.
For a preview that must not install prerequisites, use `./install.sh --no-install`.
Package installation, Nix installation, and activation each explain their changes
before asking for confirmation. Declining stops that stage.

Inspect the printed `home-files` directory to see the generated configuration.
When ready:

```sh
./install.sh --apply
```

This builds again, then requires you to type `APPLY`. It replaces any existing
standalone Home Manager profile for this account. Try it in a separate account
or VM first if you already use Home Manager. Unmanaged conflicting files are
backed up with a unique `.commander-os-…` suffix; Home Manager performs its own
collision checks. A build preview does not perform those activation checks.
After activation, accept the default **Y** at the Fish login-shell prompt.
The installer verifies Fish, registers its stable Nix profile path in `/etc/shells`,
and uses `sudo chsh` to set it for your account. Log out of the desktop and back
in for new terminals to inherit it. Run `fish` to try it immediately. A terminal
profile configured to run Bash explicitly must be changed to use the default shell.
Bash is only used to launch the installer on a fresh system; your interactive
configuration, prompt, fzf and zoxide integrations target Fish.

## Privacy and reproducibility

Machine settings live outside the checkout. The installer copies only the flake,
lock file, example settings and modules into a temporary build tree, then adds
validated machine settings. This avoids Git's untracked-file filtering without
requiring personal settings in commits. Nix stores usernames and home paths in
its normally readable store: **never put secrets in Nix configuration**.

The example account is only for validation. Use the installer for your account;
do not directly activate the flake's example configuration. The tracked lock
file pins Nixpkgs and Home Manager. Preserve `home.stateVersion` when upgrading.

## Updates and rollback

Pull source updates and preview before applying:

```sh
git pull --ff-only
./install.sh
./install.sh --apply
```

Maintainers can update dependencies with `nix flake update`, then run the checks
below before committing the changed lock file.

Before replacing an existing profile, record `home-manager generations` and keep
your old configuration checkout. To roll back, find the previous generation
using `home-manager generations` and run its `/nix/store/…-home-manager-generation/activate`
script. Then restore any unmanaged files from their `.commander-os-…` backups as
needed. Generation rollback does not automatically restore those backup files.
Before uninstalling or disabling Fish, change your login shell back using
`chsh -s /bin/bash` (or the path saved in
`~/.local/state/commander-os/previous-shell.txt`). The Fish login shell relies on
the Home Manager profile remaining installed. Generation rollback does not undo
`chsh` or the `/etc/shells` entry.
On a first installation there may be no previous generation; use
`home-manager uninstall`, inspect the affected files, and restore the backups.

See the [Home Manager manual](https://nix-community.github.io/home-manager/) for
profile management. Avoid garbage-collecting previous generations while testing.

## Support and development

The target architectures are x86_64 and aarch64 Linux. The initial build is
validated on x86_64; fresh-machine, ARM and cross-distribution activation testing
are still pending. NixOS users should avoid managing the same home with both a
system Home Manager module and this standalone installer. macOS is not supported.

```sh
python3 -B -m unittest discover -s tests -v
bash -n install.sh scripts/prerequisites.sh
nix --extra-experimental-features 'nix-command flakes' flake check
```

Planned next steps: clean-VM installation tests, optional desktop styling, and
optional backup integrations with user-provided destinations and credentials.
No personal repository history, system snapshots, wallet data, or bundled
executables are included.

The guided dependency setup is inspired by the workflow of
[ChrisTitusTech/mybash](https://github.com/ChrisTitusTech/mybash); Commander-os
uses its own installer and manages the home environment through Home Manager.

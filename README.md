# Commander-os

A portable Linux home environment built with Nix and Home Manager. This is an
initial starter, not an operating-system image or a distribution installer.

The default setup provides Fish, Starship, Neovim, fuzzy finding, directory
navigation, and common CLI tools. Git and Lazygit are optional. It does not change
your bootloader, desktop, login shell, distribution packages, or backup services.

## Get started

Requirements: Linux, Git, Python 3, internet access and a working Nix installation.
Home Manager itself does not need to be installed beforehand.

```sh
git clone https://github.com/Commanderx-code/Commander-os.git
cd Commander-os
./install.sh --init
```

Edit `~/.config/commander-os/machine.json` (or the path printed by the installer).
Set `fish`, `neovim`, and `development` to `true` or `false` to select features.
Defaults come from your current account. Never run the installer with sudo.

If Nix is missing, follow the [official Nix installation guide](https://nixos.org/download/).
The script also prints guidance when it cannot find Nix. Installation choices
vary with systemd, SELinux and your host OS; it does not silently install system
services. Open a fresh terminal after installing Nix.

Build without changing your active configuration:

```sh
./install.sh
```

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
After activation, run `fish` to try the shell.

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
bash -n install.sh
nix --extra-experimental-features 'nix-command flakes' flake check
```

Planned next steps: clean-VM installation tests, optional desktop styling, and
optional backup integrations with user-provided destinations and credentials.
No personal repository history, system snapshots, wallet data, or bundled
executables are included.

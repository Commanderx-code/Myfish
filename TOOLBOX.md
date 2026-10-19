# Publishing tools to Helix Toolbox

`toolbox.json` is this repository's exported menu for
[Helix Toolbox](https://github.com/Commanderx-code/Helix-toolbox), which replaced
Commander Toolbox. Commit the configuration
and its catalog entry together, then push to `main`. When this repository's
`check.yml` succeeds on `main`, the **Notify Helix Toolbox** workflow starts
Helix Toolbox's source sync, which adopts the revision only after verifying that
successful check itself. Failed or unfinished checks leave the previous Helix Toolbox
source version in place. Helix Toolbox also checks on a schedule, but GitHub runs
that only every few hours.

Helix Toolbox regenerates its menus, runs compatibility tests, builds the Linux x86_64
and aarch64 applications, and publishes a release with their checksums. Existing installations pick
up the new menu after updating Helix Toolbox; run the relevant installer to apply the
configuration. Installing an application locally does not export it automatically.

## Update an existing tool

Edit its tracked configuration or installer and push normally. Built-in catalog
entries retain their dedicated Helix Toolbox installers. Myfish's shell entries run the
updated Myfish installer, including any new tools it manages.

## Export a new application configuration

Add a `config` entry to the `entries` array in `toolbox.json`. For example, after
adding an actual `configs/btop/btop.conf` file:

```json
{
  "id": "btop",
  "name": "Btop Monitor",
  "description": "Install Btop and the shared monitor configuration.",
  "type": "config",
  "packages": {
    "apt-get": ["btop"],
    "dnf": ["btop"],
    "pacman": ["btop"]
  },
  "files": [
    {"source": "configs/btop/btop.conf", "target": "btop/btop.conf"}
  ]
}
```

- `id`: stable lowercase identifier with letters, numbers and hyphens.
- `name`: unique menu label across Helix Toolbox; `description` explains the install.
- `packages`: distro package names, separately for each supported package manager.
  An empty array supports configuration-only installation on that manager; omit a
  manager to reject it. Nala uses the `apt-get` entry. Packages must exist in the
  user's enabled repositories; the installer does not add repositories.
- `files`: tracked source files or directories, relative to this repository.
  Targets are relative to `$XDG_CONFIG_HOME` (normally `~/.config`). Export only the
  configuration needed by the tool. Symlinks and paths outside the repo are rejected.

Helix Toolbox displays the new entry automatically. Its installer asks for `APPLY`,
validates all paths, installs the declared packages, then copies configuration
with backups. Home Manager-owned symlinks are refused before package changes.
Directory exports replace the destination directory with a backup; use individual
files to preserve unrelated files alongside them. Multiple file copies are not a
single transaction: earlier successful copies retain their backups if a later copy
fails.

The `builtin` type references an existing dedicated Helix Toolbox handler. Keep those
entries when editing the catalog. Tools requiring custom system services, boot
changes or a special installer still need an appropriate Helix Toolbox handler; this
catalog's generic installer manages distro packages and user configuration only.

## Check the automation

Open [Helix Toolbox source synchronization](https://github.com/Commanderx-code/Helix-toolbox/actions/workflows/sync-sources.yml).
**Run workflow** checks immediately. The workflow summary/log shows which source
revision was accepted or is waiting for CI. Builds appear under
[Helix Toolbox releases](https://github.com/Commanderx-code/Helix-toolbox/releases).
Starting that workflow from here needs the `HELIXFORGE_DISPATCH_TOKEN` secret:
a fine-grained token for Commanderx-code/Helix-toolbox with only **Actions: Read
and write**. [Helix Toolbox's sync guide](https://github.com/Commanderx-code/Helix-toolbox/blob/main/docs/SOURCE-SYNC.md#notifications-from-the-sources)
shows how to create it. Without it, the notifier only leaves a notice and
Helix Toolbox adopts the revision on its next push or scheduled run.

GitHub disables scheduled workflows in public repos after 60 days without repo
activity; re-enable the workflow in Actions if necessary. New source repositories
must be explicitly connected to the sync workflow; it watches dotfiles and Myfish.

## Shared Fish source of truth

Myfish owns the portable functions in `modules/fish/functions/`. Edit and push a
shared function here once. After Linux and both Mac CI jobs pass, dotfiles'
[shared Fish importer](https://github.com/Commanderx-code/dotfiles/actions/workflows/sync-myfish.yml)
automatically imports the tested functions, preserving its explicit workstation
overrides. It checks every recorded import hash, tests/builds the combined
configuration, and publishes its own validated commit. Helix Toolbox then adopts the
tested Myfish and dotfiles revisions through its existing schedule.

New portable functions are included automatically unless their name conflicts
with a dotfiles-owned function. Startup snippets and machine-specific functions
retain their repository ownership. Do not edit generated Myfish copies in
dotfiles; fix shared behavior here so Linux and macOS CI can validate it.

See the [complete sync guide](https://github.com/Commanderx-code/dotfiles/blob/main/FISH-SYNC.md)
for timing, override ownership, local checkout updates, and recovery.

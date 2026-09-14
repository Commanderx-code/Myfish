#!/usr/bin/env python3
"""Preview, remove, reinstall, or detach a Commander-os installation."""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

import bootstrap
import install_state
import native

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {'shell', 'neovim', 'development'}


def safe_path(path):
    path = Path(path)
    home = Path.home()
    if not path.is_absolute() or '..' in path.parts or path == home or not path.is_relative_to(home):
        raise ValueError(f'Refusing path outside home: {path}')
    if any(p.is_symlink() for p in path.parents if p != home and p.is_relative_to(home)):
        raise ValueError(f'Refusing symlinked parent: {path}')
    return path


def generation():
    state = install_state.directory().parent
    paths = [state / 'nix/profiles/home-manager', state / 'home-manager/profiles/home-manager',
             Path('/nix/var/nix/profiles/per-user') / pwd.getpwuid(os.getuid()).pw_name / 'home-manager']
    found = {p.resolve() for p in paths if p.exists()}
    if len(found) > 1:
        raise RuntimeError('Conflicting Home Manager profiles found; resolve them before removal.')
    return next(iter(found), None)


def shell_choice(machine):
    return machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')


def component(path):
    relative = Path(path).relative_to(Path.home())
    if 'nvim' in relative.parts:
        return 'neovim'
    if 'lazygit' in relative.parts or Path(path).name == '.gitconfig':
        return 'development'
    return 'shell'


def discover(config):
    receipt = install_state.load()
    machine = bootstrap.validate(json.loads(config.read_text())) if config.exists() else receipt.get('machine')
    if not machine:
        raise RuntimeError('No saved Commander-os settings found. Use --config PATH if needed.')
    bootstrap.validate(machine)
    if machine['homeDirectory'] != str(Path.home()) or machine['username'] != pwd.getpwuid(os.getuid()).pw_name:
        raise ValueError('Settings must match the current user and home directory.')
    active = generation()
    if receipt.get('pending'):
        if active != Path(receipt['generation']):
            command = shlex.quote(str(Path(receipt['recovery']) / 'generation/activate'))
            raise RuntimeError(f'Previous maintenance is incomplete. Restore with HOME_MANAGER_BACKUP_EXT=commander-recovery {command}')
        receipt.pop('pending')
    if active:
        if receipt.get('generation') != str(active):
            # Legacy releases had no receipt. Require both project-specific assets.
            for name in ('.local/bin/fzf-preview', '.config/starship.toml'):
                source = ROOT / ('modules/fzf-preview' if name.endswith('fzf-preview') else 'modules/starship.toml')
                installed = active / 'home-files' / name
                if not installed.is_file():
                    raise RuntimeError('The active Home Manager generation is not recognizable as Commander-os.')
                # HM serializes TOML, so the preview is the exact fingerprint; Starship must have our format.
                if name.endswith('fzf-preview') and installed.read_bytes() != source.read_bytes():
                    raise RuntimeError('Refusing to remove an unrecognized Home Manager generation.')
                if name.endswith('starship.toml') and '╭' not in installed.read_text() and '\\u256d' not in installed.read_text().lower():
                    raise RuntimeError('Home Manager theme does not match the Commander-os setup.')
        receipt.update(backend='home-manager', generation=str(active), machine=machine)
    elif receipt.get('backend') == 'home-manager':
        raise RuntimeError('The recorded Home Manager generation is no longer active; refusing stale removal.')
    elif not receipt.get('backend'):
        receipt.update(backend='native', machine=machine, legacy=True)
        config_home = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
        for shell in ('bash', 'fish', 'zsh'):
            sample = copy.deepcopy(machine)
            sample['shell'] = shell
            sample['features']['neovim'] = False
            for path, text in native.config_files(sample, Path.home(), config_home).items():
                if path.name not in ('.bashrc', '.zshrc') and path.is_file() and not path.is_symlink() and path.read_text() == text:
                    receipt['files'][str(path)] = {'original': None, 'mode': None, 'installed': install_state.digest(path)}
        if not receipt['files']:
            raise RuntimeError('No recorded or recognizable Commander-os installation found.')
    return receipt, machine


def managed_files(active):
    result = []
    for source in (active / 'home-files').rglob('*'):
        if source.is_symlink() or source.is_file():
            target = safe_path(Path.home() / source.relative_to(active / 'home-files'))
            if target.is_symlink() and target.resolve() == source.resolve():
                result.append(target)
            elif target.exists():
                print(f'Keep independently changed file: {target}')
    return result


def copy_path(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=False)
        for path in [target, *target.rglob('*')]:
            path.chmod(path.stat().st_mode | (0o700 if path.is_dir() else 0o200))
    else:
        shutil.copy2(source, target, follow_symlinks=True)
        target.chmod(target.stat().st_mode | 0o200)


def recovery(files, receipt):
    directory = install_state.directory() / f'recovery-{time.time_ns()}'
    directory.mkdir(parents=True, mode=0o700)
    for path in files:
        safe_path(path)
        if path.exists():
            copy_path(path, directory / 'files' / path.relative_to(Path.home()))
    (directory / 'installation.json').write_text(json.dumps(receipt, indent=2))
    print(f'Recovery backup: {directory}', flush=True)
    return directory


def fallback_shell():
    previous = install_state.directory() / 'previous-shell.txt'
    shell = previous.read_text().strip() if previous.exists() else '/bin/bash'
    if not shell.startswith(('/bin/', '/usr/bin/')) or not os.access(shell, os.X_OK):
        shell = '/bin/bash'
    if not os.access(shell, os.X_OK) or shell not in Path('/etc/shells').read_text().splitlines():
        raise RuntimeError('Register a working system shell in /etc/shells before removal.')
    return shell


def set_login(shell):
    account = pwd.getpwuid(os.getuid())
    if account.pw_shell != shell:
        if not os.access(shell, os.X_OK) or shell not in Path('/etc/shells').read_text().splitlines():
            raise RuntimeError(f'Cannot use login shell: {shell}')
        subprocess.run(['sudo', 'chsh', '-s', shell, account.pw_name], check=True)


def nix_tool(name):
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f'{name} is required for Home Manager maintenance.')
    return str(Path(executable).resolve())


def modern_profile():
    return any((p / 'manifest.json').exists() for p in [Path.home() / '.nix-profile', install_state.directory().parent / 'nix/profile'])


def build_hm(machine, active, detach, directory):
    if active.parent != Path('/nix/store') or not re.fullmatch(r'[a-zA-Z0-9._-]+', active.name):
        raise ValueError('Invalid active Nix generation')
    shutil.copy2(ROOT / 'scripts/maintenance.nix', directory / 'flake.nix')
    shutil.copy2(ROOT / 'flake.lock', directory / 'flake.lock')
    (directory / 'machine.json').write_text(json.dumps(machine))
    (directory / 'generation.json').write_text(json.dumps(str(active)))
    result = []
    for name in (['remove', 'retained'] if detach else ['remove']):
        command = [nix_tool('nix'), '--extra-experimental-features', 'nix-command flakes', 'build',
                   '--no-write-lock-file', '--no-link', '--print-out-paths',
                   *(['--impure'] if name == 'retained' else []), f'path:{directory}#{name}']
        output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
        path = Path(output.stdout.strip())
        if path.parent != Path('/nix/store') or not path.is_dir():
            raise RuntimeError('Nix returned an invalid maintenance build')
        result.append(path)
    return result


def remove_hm(receipt, machine, detach, apply):
    active = Path(receipt['generation'])
    files = managed_files(active)
    original_shell = pwd.getpwuid(os.getuid()).pw_shell
    fallback = fallback_shell()
    originals = {}
    if not detach:
        for path in files:
            prefix = path.name + '.commander-os-'
            candidates = [p for p in path.parent.glob(prefix + '*') if p.name[len(prefix):].isdigit()]
            if candidates:
                originals[path] = min(candidates, key=lambda p: int(p.name[len(prefix):]))
    print('Remove this entire Home Manager generation and its generation history:', active)
    print('First protect a recovery generation and switch the login shell to:', fallback)
    for path in files:
        print(('Keep editable copy: ' if detach else 'Remove managed link: ') + str(path))
    for path, backup in originals.items():
        print(f'Restore earlier backup: {backup} -> {path}')
    if detach:
        print('Keep current tools, fonts and plugins as a fixed Nix snapshot. Nix stays installed.')
        print('Home Manager stops managing configuration. This does not migrate packages to apt/dnf/pacman.')
    if not apply:
        return False
    # Resolve the tools before removing a profile that may supply those tools.
    store = nix_tool('nix-store')
    install_command = ([nix_tool('nix'), '--extra-experimental-features', 'nix-command flakes', 'profile', 'install']
                       if modern_profile() else [nix_tool('nix-env'), '--install'])
    with tempfile.TemporaryDirectory(prefix='commander-maintenance-') as temp:
        built = build_hm(machine, active, detach, Path(temp))
        word = 'DETACH' if detach else 'REMOVE'
        if input(f'Type {word} to apply this plan: ') != word:
            print('Cancelled.')
            return False
        if generation() != active:
            raise RuntimeError('The active generation changed during planning. Rerun maintenance.')
        backup = recovery(files, receipt)
        subprocess.run([store, '--realise', str(active), '--add-root', str(backup / 'generation')], check=True)
        if detach:
            subprocess.run([store, '--realise', str(built[1]), '--add-root', str(backup / 'retained')], check=True)
        set_login(fallback)
        # Journal where to recover even if the upstream activation fails midway.
        pending = dict(receipt, recovery=str(backup), pending='detach' if detach else 'remove')
        install_state.save(pending)
        try:
            subprocess.run([str(built[0] / 'activate')], check=True)
            updated = {'version': 1, 'backend': 'removed', 'machine': machine,
                       'files': {}, 'packages': [], 'recovery': str(backup)}
            if detach:
                subprocess.run([*install_command, str(built[1])], check=True)
                for path in files:
                    if path.exists() or path.is_symlink():
                        raise RuntimeError(f'Unexpected file after Home Manager removal: {path}')
                    copy_path(backup / 'files' / path.relative_to(Path.home()), path)
                    for item in (path.rglob('*') if path.is_dir() else [path]):
                        if item.is_file():
                            updated['files'][str(item)] = {'original': None, 'mode': None, 'installed': install_state.digest(item)}
                updated.update(backend='detached', retained=str(built[1]))
            else:
                for path, old in originals.items():
                    if not path.exists() and not path.is_symlink():
                        path.parent.mkdir(parents=True, exist_ok=True)
                        if old.is_symlink():
                            path.symlink_to(os.readlink(old))
                        else:
                            copy_path(old, path)
            install_state.save(updated)
            if detach and os.access(original_shell, os.X_OK) and original_shell in Path('/etc/shells').read_text().splitlines():
                set_login(original_shell)
        except (OSError, RuntimeError, subprocess.CalledProcessError, KeyboardInterrupt):
            command = f'HOME_MANAGER_BACKUP_EXT=commander-recovery-{time.time_ns()} ' + shlex.quote(str(backup / 'generation/activate'))
            print(f'Maintenance stopped. Recovery backup: {backup}\nRestore the previous generation with:\n{command}', file=sys.stderr)
            raise
    print('Home Manager removed. Reopen your terminal.' if detach else 'Commander-os removed; Nix and recovery backups retained.')
    return True


def strip_startup(text):
    lines = text.splitlines(keepends=True)
    result = []
    index = 0
    while index < len(lines):
        if lines[index].strip() == '# Commander-os shell integration' and index + 1 < len(lines):
            next_line = lines[index + 1]
            entries = [f'[ -r "${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/init.{shell}" ] && . "${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/init.{shell}"' for shell in ('bash', 'zsh')]
            if next_line.rstrip('\n') in entries:
                index += 2
                continue
        result.append(lines[index])
        index += 1
    return ''.join(result)


def remove_native(receipt, components, apply):
    if receipt.get('backend') == 'detached' and components != COMPONENTS:
        raise RuntimeError('Detached packages are one snapshot. Reinstall with Home Manager to select individual components.')
    files = {safe_path(p): record for p, record in receipt['files'].items() if component(p) in components}
    edits = {}
    if 'shell' in components and receipt.get('backend') != 'detached':
        for name in ('.bashrc', '.zshrc'):
            path = safe_path(Path.home() / name)
            if path.is_file() and not path.is_symlink():
                old = path.read_text()
                new = strip_startup(old)
                tracked = files.get(path)
                unchanged = tracked and install_state.digest(path) == tracked['installed']
                if old != new and not unchanged:
                    edits[path] = new
    for path, record in files.items():
        unchanged = path.is_file() and not path.is_symlink() and install_state.digest(path) == record['installed']
        print(f'{path}: ' + ('restore original/remove installed file' if unchanged else 'KEEP changed/missing/symlinked file'))
    for path in edits:
        print(f'{path}: remove Commander-os startup entry; keep other content')
    eligible = receipt.get('packages', []) if components == COMPONENTS else [p for p in receipt.get('packages', []) if p == 'neovim' and 'neovim' in components]
    fallback = fallback_shell() if 'shell' in components else None
    eligible = [p for p in eligible if p not in ('bash', Path(fallback).name if fallback else 'bash')]
    if any(not isinstance(p, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9+_.:-]*', p) for p in eligible):
        raise ValueError('Invalid package name in installation record')
    print('Optional recorded package removal:', ', '.join(eligible) or 'none')
    if receipt.get('legacy'):
        print('Older install: unknown packages and original-file backups are preserved because ownership was not recorded.')
    if receipt.get('backend') == 'detached':
        print('Remove the retained Nix profile entry. Recovery roots and personal files stay.')
    if not apply:
        return False
    selected = []
    if eligible:
        answer = input('Packages to remove [none/all/space-separated names; default none]: ').strip()
        selected = eligible if answer == 'all' else ([] if answer in ('', 'none') else answer.split())
        if not set(selected) <= set(eligible):
            raise ValueError('Only packages in the recorded list can be removed.')
    print('Selected package removal:', ', '.join(selected) or 'none')
    if input('Type REMOVE to apply this plan: ') != 'REMOVE':
        print('Cancelled.')
        return False
    backup = recovery([p for p in set(files) | set(edits) if p.is_file() and not p.is_symlink()], receipt)
    if fallback:
        set_login(fallback)
    if selected:
        command = {'apt-get': ['sudo', 'apt-get', 'remove'],
                   'dnf': ['sudo', 'dnf', '--setopt=clean_requirements_on_remove=False', 'remove'],
                   'pacman': ['sudo', 'pacman', '-R']}[receipt['manager']]
        print('Review and confirm the package manager transaction. Dependencies are not auto-removed.')
        subprocess.run([*command, *selected], check=True)
        # Some managers return success on cancellation; check what actually disappeared.
        receipt['packages'] = [p for p in receipt['packages'] if p not in selected or native.package_installed(receipt['manager'], p)]
        install_state.save(receipt)
    if receipt.get('backend') == 'detached':
        command = ([nix_tool('nix'), '--extra-experimental-features', 'nix-command flakes', 'profile', 'remove', receipt['retained']]
                   if modern_profile() else [nix_tool('nix-env'), '--uninstall', 'commander-os-retained'])
        subprocess.run(command, check=True)
        receipt['backend'] = 'removed'
        install_state.save(receipt)
    for path, record in files.items():
        if path in edits or not path.is_file() or path.is_symlink() or install_state.digest(path) != record['installed']:
            continue
        if record['original'] is None:
            path.unlink()
            if path.name == 'init.lua' and path.parent.name == 'nvim':
                try:
                    path.parent.rmdir()  # Allow reinstall into a directory we left empty.
                except OSError:
                    pass
        else:
            path.write_bytes(base64.b64decode(record['original'], validate=True))
            path.chmod(record['mode'])
        receipt['files'].pop(str(path), None)
        install_state.save(receipt)
    for path, text in edits.items():
        path.write_text(text)
        receipt['files'].pop(str(path), None)
    if not receipt['files'] and not receipt.get('packages'):
        receipt['backend'] = 'removed'
    receipt['recovery'] = str(backup)
    install_state.save(receipt)
    print('Removal finished. Edited files, history, settings and recovery backups were preserved.')
    return True


def reinstall(receipt, machine, config, components, remove, apply, selective):
    updated = copy.deepcopy(machine)
    if 'shell' in components:
        if remove:
            updated['shell'] = 'keep'
        elif apply:
            choice = input('Shell [bash/fish/zsh/keep; Enter keeps saved choice]: ').strip()
            if choice:
                if choice not in ('bash', 'fish', 'zsh', 'keep'):
                    raise ValueError('Invalid shell')
                updated['shell'] = choice
        updated['features']['fish'] = shell_choice(updated) == 'fish'
    for feature in ('neovim', 'development'):
        if feature in components and (remove or selective):
            updated['features'][feature] = not remove
    backend = receipt['backend']
    if backend in ('removed', 'detached'):
        if not apply:
            print('Reinstall will ask for home-manager or native mode; a detached snapshot must be removed first.')
            return
        backend = input('Reinstall backend [home-manager/native]: ').strip()
        if backend not in ('home-manager', 'native'):
            raise ValueError('Invalid backend')
    print('Reapply saved configuration using', backend, 'with these settings:')
    print(json.dumps(updated, indent=2))
    print('Reinstall ensures tools/configuration are present; it does not erase history or force-download working packages.')
    if not apply or input('Type REINSTALL to continue: ') != 'REINSTALL':
        return
    if receipt['backend'] == 'detached':
        print('First remove the detached snapshot, with another preview and backup.')
        if not remove_native(receipt, COMPONENTS, True):
            return
    if remove and 'shell' in components:
        set_login(fallback_shell())
    with tempfile.TemporaryDirectory(prefix='commander-reinstall-') as temp:
        staged = Path(temp) / 'machine.json'
        staged.write_text(json.dumps(updated))
        subprocess.run([str(ROOT / 'install.sh'), '--apply', '--backend', backend, '--config', str(staged)], check=True)
    actual = install_state.load()
    if actual.get('machine') == updated and actual.get('backend') == backend:
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps(updated, indent=2) + '\n')


def menu():
    print('Commander-os maintenance\n'
          '  1) Uninstall all Commander-os components\n'
          '  2) Reinstall the saved setup\n'
          '  3) Choose components to remove\n'
          '  4) Choose components to reinstall\n'
          '  5) Remove Home Manager, keep my setup (Nix stays)\n'
          '  6) Show installation status\n'
          '  0) Cancel')
    choice = input('Choose [0-6]: ').strip()
    if choice in ('', '0'):
        return None
    actions = {'1': 'remove', '2': 'reinstall', '3': 'remove', '4': 'reinstall', '5': 'detach', '6': 'status'}
    if choice not in actions:
        raise ValueError('Invalid choice')
    components = input('Components [shell,neovim,development; comma separated]: ').strip() if choice in ('3', '4') else 'all'
    return actions[choice], components


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('remove', 'reinstall', 'detach', 'status'))
    parser.add_argument('--components', default='all', help='all or comma-separated shell,neovim,development')
    parser.add_argument('--apply', action='store_true', help='ask for confirmation; explicit CLI actions default to preview')
    parser.add_argument('--config', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'commander-os/machine.json')
    args = parser.parse_args()
    if sys.platform != 'linux' or os.geteuid() == 0:
        raise ValueError('Run as your normal Linux user, without sudo.')
    os.umask(0o077)
    if not args.action:
        if not sys.stdin.isatty():
            raise ValueError('Specify --action when running without a terminal.')
        choice = menu()
        if not choice:
            return 0
        args.action, args.components = choice
        args.apply = args.action != 'status'
    components = COMPONENTS if args.components == 'all' else set(args.components.split(','))
    if not components or not components <= COMPONENTS:
        raise ValueError('Select all or shell,neovim,development.')
    if args.apply and not sys.stdin.isatty():
        raise ValueError('Apply requires an interactive terminal for confirmation.')
    receipt, machine = discover(args.config)
    print('Detected:', receipt['backend'])
    print('Scope: Commander-os for this account. Nix, personal files and recovery backups stay.')
    if receipt.get('pending'):
        raise RuntimeError(f"A previous operation stopped partway through. Restore its generation first: {receipt.get('recovery')}/generation/activate")
    if args.action == 'status':
        print(json.dumps({'backend': receipt['backend'], 'machine': machine, 'recorded_files': len(receipt['files']), 'recorded_packages': receipt['packages']}, indent=2))
    elif args.action == 'detach':
        if receipt['backend'] != 'home-manager':
            raise RuntimeError('Detach requires an active Commander-os Home Manager installation.')
        remove_hm(receipt, machine, True, args.apply)
    elif args.action == 'reinstall':
        reinstall(receipt, machine, args.config, components, False, args.apply, args.components != 'all')
    elif receipt['backend'] == 'home-manager':
        if components == COMPONENTS:
            remove_hm(receipt, machine, False, args.apply)
        else:
            reinstall(receipt, machine, args.config, components, True, args.apply, True)
    else:
        remove_native(receipt, components, args.apply)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        print(f'Commander-os: {error}', file=sys.stderr)
        sys.exit(1)

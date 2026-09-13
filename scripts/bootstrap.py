#!/usr/bin/env python3
"""Build a private, curated Home Manager source tree; activate only on request."""
import argparse
import json
import os
from pathlib import Path
import platform
import pwd
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ('fish', 'neovim', 'development')


def validate(machine):
    if set(machine) != {'username', 'homeDirectory', 'system', 'features'}:
        raise ValueError('Machine settings must contain only username, homeDirectory, system, features')
    if not isinstance(machine['username'], str) or not machine['username'] or '/' in machine['username']:
        raise ValueError('Invalid username')
    if not isinstance(machine['homeDirectory'], str) or not machine['homeDirectory'].startswith('/'):
        raise ValueError('homeDirectory must be an absolute path')
    if machine['system'] not in ('x86_64-linux', 'aarch64-linux'):
        raise ValueError('Supported architectures: x86_64-linux and aarch64-linux')
    if not isinstance(machine['features'], dict) or set(machine['features']) != set(FEATURES):
        raise ValueError('features must contain fish, neovim, development')
    if any(type(v) is not bool for v in machine['features'].values()):
        raise ValueError('Feature values must be true or false')
    return machine


def stage(destination, machine):
    # Explicit allowlist: never send arbitrary checkout/private files to the Nix store.
    for name in ('flake.nix', 'flake.lock', 'machine.example.json'):
        shutil.copyfile(ROOT / name, destination / name)
    shutil.copytree(ROOT / 'modules', destination / 'modules')
    (destination / 'machine.json').write_text(json.dumps(validate(machine), indent=2) + '\n')


def default_machine():
    return validate({
        'username': pwd.getpwuid(os.getuid()).pw_name,
        'homeDirectory': str(Path.home()),
        'system': platform.machine() + '-linux',
        'features': {'fish': True, 'neovim': True, 'development': False},
    })


def configure_fish_login(machine):
    if not machine['features']['fish']:
        return
    # Keep the profile path: resolving to a versioned store path breaks upgrades.
    candidates = [Path(machine['homeDirectory']) / '.nix-profile/bin/fish',
                  Path(os.environ.get('XDG_STATE_HOME', str(Path(machine['homeDirectory']) / '.local/state'))) / 'nix/profile/bin/fish']
    fish = next((p for p in candidates if os.access(p, os.X_OK)), None)
    if fish is None:
        raise RuntimeError('Home Manager activated, but Fish was not found in the Nix profile; login shell unchanged')
    subprocess.run([str(fish), '--no-config', '-c', 'exit 0'], check=True)
    account = pwd.getpwuid(os.getuid())
    if account.pw_shell == str(fish):
        print('Fish is already your login shell.')
        return
    print(f'Fish is installed at {fish}. Previous login shell: {account.pw_shell}')
    if input('Make Fish your default login shell? [Y/n] ').strip().lower() not in ('', 'y', 'yes'):
        print('Login shell unchanged. Run fish to start it manually.')
        return
    if not shutil.which('sudo') or not shutil.which('chsh'):
        raise RuntimeError('Fish is installed, but sudo and chsh are required to set the login shell')
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'commander-os'
    state.mkdir(parents=True, exist_ok=True)
    previous = state / 'previous-shell.txt'
    if not previous.exists():
        with previous.open('x') as target:
            target.write(account.pw_shell + '\n')
    shells = Path('/etc/shells').read_text().splitlines()
    if str(fish) not in shells:
        subprocess.run(['sudo', 'tee', '-a', '/etc/shells'], input='\n' + str(fish) + '\n',
                       text=True, stdout=subprocess.DEVNULL, check=True)
    subprocess.run(['sudo', 'chsh', '-s', str(fish), account.pw_name], check=True)
    print('Fish is now your login shell. Log out of the desktop and log back in.\n'
          f'Previous shell saved at {previous}. Terminal custom-command settings can override the login shell.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='build, then ask before activating')
    parser.add_argument('--init', action='store_true', help='create settings only; do not build')
    parser.add_argument('--config', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'commander-os/machine.json')
    args = parser.parse_args()
    if platform.system() != 'Linux' or os.geteuid() == 0:
        raise ValueError('Run as your normal user on Linux, without sudo')
    os.umask(0o077)
    if args.config.exists():
        machine = validate(json.loads(args.config.read_text()))
    else:
        machine = default_machine()
        args.config.parent.mkdir(parents=True, exist_ok=True)
        with args.config.open('x') as target:
            target.write(json.dumps(machine, indent=2) + '\n')
        print(f'Created settings: {args.config}', flush=True)
    print('Features: ' + ', '.join(k for k, v in machine['features'].items() if v), flush=True)
    if args.init:
        return 0
    if not shutil.which('nix'):
        print('Nix is required; Home Manager does not need to be installed first.\n'
              'Follow https://nixos.org/download/ for your system.\n'
              'For Linux with systemd and SELinux disabled, the official multi-user command is:\n'
              "  curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install | sh -s -- --daemon\n"
              'Then open a new terminal and rerun ./install.sh.', file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix='commander-os-') as directory:
        source = Path(directory)
        stage(source, machine)
        command = ['nix', '--extra-experimental-features', 'nix-command flakes', 'build',
                   '--no-write-lock-file', '--no-link', '--print-out-paths',
                   f'path:{source}#homeConfigurations.commander.activationPackage']
        print('Building preview; your live configuration will not change during the build.', flush=True)
        result = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE)
        package = Path(result.stdout.strip())
        if not package.is_absolute() or not (package / 'activate').is_file():
            raise RuntimeError('Nix did not return a valid activation package')
        print(f'Built: {package}\nManaged files: {package}/home-files', flush=True)
        if not args.apply:
            print('Preview complete. Inspect home-files, edit your settings, then run ./install.sh --apply.')
            return 0
        if machine['username'] != pwd.getpwuid(os.getuid()).pw_name or machine['homeDirectory'] != str(Path.home()):
            raise ValueError('Activation settings must match the current user and home directory')
        print('This replaces your active Home Manager configuration, if any.\n'
              'Existing unmanaged conflicts will receive a unique backup suffix.\n'
              'Review the built home-files and README rollback instructions before continuing.')
        if input('Type APPLY to activate: ') != 'APPLY':
            print('Cancelled; no activation performed.')
            return 0
        env = dict(os.environ, HOME_MANAGER_BACKUP_EXT=f'commander-os-{time.time_ns()}')
        subprocess.run([str(package / 'activate')], env=env, check=True)
        print('Home Manager activated successfully.')
        configure_fish_login(machine)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        print(f'Commander-os: {error}', file=sys.stderr)
        sys.exit(1)

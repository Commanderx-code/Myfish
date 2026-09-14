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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_state
import host

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ('fish', 'neovim', 'development')


def validate(machine):
    if set(machine) - {'username', 'homeDirectory', 'system', 'features', 'shell'} or not {'username', 'homeDirectory', 'system', 'features'} <= set(machine):
        raise ValueError('Machine settings must contain only username, homeDirectory, system, features')
    if not isinstance(machine['username'], str) or not machine['username'] or '/' in machine['username']:
        raise ValueError('Invalid username')
    if not isinstance(machine['homeDirectory'], str) or not machine['homeDirectory'].startswith('/'):
        raise ValueError('homeDirectory must be an absolute path')
    if machine['system'] not in ('x86_64-linux', 'aarch64-linux', 'x86_64-darwin', 'aarch64-darwin'):
        raise ValueError('Supported systems: x86_64/aarch64 Linux and macOS')
    if not isinstance(machine['features'], dict) or set(machine['features']) != set(FEATURES):
        raise ValueError('features must contain fish, neovim, development')
    if any(type(v) is not bool for v in machine['features'].values()):
        raise ValueError('Feature values must be true or false')
    if machine.get('shell', 'fish' if machine['features']['fish'] else 'keep') not in ('bash', 'fish', 'zsh', 'keep'):
        raise ValueError('shell must be bash, fish, zsh or keep')
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
        'system': host.system(),
        'features': {'fish': True, 'neovim': True, 'development': False},
    })


def configure_shell_login(machine, native=False):
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    if shell == 'keep':
        return
    # Keep the profile path: resolving to a versioned store path breaks upgrades.
    candidates = [Path(machine['homeDirectory']) / f'.nix-profile/bin/{shell}',
                  Path(os.environ.get('XDG_STATE_HOME', str(Path(machine['homeDirectory']) / '.local/state'))) / f'nix/profile/bin/{shell}']
    if native:
        candidates = host.native_shell_paths(shell)
    fish = next((p for p in candidates if os.access(p, os.X_OK)), None)
    if fish is None:
        raise RuntimeError(f'{shell} was not found in the installed shell paths; login shell unchanged')
    subprocess.run([str(fish), *({'fish': ['--no-config'], 'bash': ['--noprofile', '--norc'], 'zsh': ['-f']}[shell]), '-c', 'exit 0'], check=True)
    account = pwd.getpwuid(os.getuid())
    if account.pw_shell == str(fish):
        print(f'{shell} is already your login shell.')
        return
    print(f'{shell} is installed at {fish}. Previous login shell: {account.pw_shell}')
    if input(f'Make {shell} your default login shell? [Y/n] ').strip().lower() not in ('', 'y', 'yes'):
        print(f'Login shell unchanged. Run {shell} to start it manually.')
        return
    if not shutil.which('sudo') or not shutil.which('chsh'):
        raise RuntimeError(f'{shell} is installed, but sudo and chsh are required to set the login shell')
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
    print(f'{shell} is now your login shell. Log out of the desktop and log back in.\n'
          f'Previous shell saved at {previous}. Terminal custom-command settings can override the login shell.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=['home-manager', 'native'], default='home-manager')
    parser.add_argument('--no-install', action='store_true')
    parser.add_argument('--shell', choices=['bash', 'fish', 'zsh', 'keep'])
    parser.add_argument('--apply', action='store_true', help='build, then ask before activating')
    parser.add_argument('--init', action='store_true', help='create settings only; do not build')
    parser.add_argument('--config', type=Path, default=Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'commander-os/machine.json')
    args = parser.parse_args()
    if platform.system() not in ('Linux', 'Darwin') or os.geteuid() == 0:
        raise ValueError('Run as your normal user on Linux or macOS, without sudo')
    os.umask(0o077)
    if args.config.exists():
        machine = validate(json.loads(args.config.read_text()))
    else:
        machine = default_machine()
        args.config.parent.mkdir(parents=True, exist_ok=True)
        with args.config.open('x') as target:
            target.write(json.dumps(machine, indent=2) + '\n')
        print(f'Created settings: {args.config}', flush=True)
    if args.shell:
        machine['shell'] = args.shell
        machine['features']['fish'] = args.shell == 'fish'
        validate(machine)
        args.config.write_text(json.dumps(machine, indent=2) + '\n')
    print('Shell: ' + machine.get('shell', 'fish' if machine['features']['fish'] else 'keep'), flush=True)
    print('Features: ' + ', '.join(k for k, v in machine['features'].items() if v), flush=True)
    if args.init:
        return 0
    if args.backend == 'native':
        from native import install_native
        return install_native(machine, apply=args.apply, install_missing=not args.no_install, configure_login=configure_shell_login)
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
        install_state.save({'version': 1, 'backend': 'home-manager', 'machine': machine,
                            'generation': str(package), 'files': {}, 'packages': []})
        print('Home Manager activated successfully.')
        configure_shell_login(machine)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, EOFError, KeyboardInterrupt) as error:
        print(f'Commander-os: {error}', file=sys.stderr)
        sys.exit(1)

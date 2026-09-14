"""Direct installation without Nix or Home Manager."""
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_state


def package_plan(machine, manager):
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    tools = {'rg': 'ripgrep', 'fd': 'fd-find' if manager == 'apt-get' else 'fd-find' if manager == 'dnf' else 'fd',
             'bat': 'bat', 'eza': 'eza', 'jq': 'jq', 'fzf': 'fzf', 'zoxide': 'zoxide', 'curl': 'curl', 'tar': 'tar'}
    if shell != 'keep':
        tools[shell] = shell
    if shell != 'keep':
        tools.update({'file': 'file', 'trash': 'trash-cli', 'unzip': 'unzip', 'chafa': 'chafa', 'git': 'git'})
    if shell == 'bash' and not (Path(machine['homeDirectory']) / '.local/share/blesh/ble.sh').is_file():
        tools.update({'git': 'git', 'make': 'make', 'gawk': 'gawk'})
    if machine['features']['neovim']:
        tools['nvim'] = 'neovim'
    if machine['features']['development']:
        tools['git'] = 'git'
    return sorted(set(package for tool, package in tools.items()
                      if (not shutil.which(tool) or (tool == shell and not any(os.access(Path(base) / shell, os.X_OK) for base in ('/usr/bin', '/bin')))) and not (tool == 'fd' and shutil.which('fdfind'))
                      and not (tool == 'bat' and shutil.which('batcat'))))


def package_installed(manager, name):
    command = {'apt-get': ['dpkg-query', '-W', '-f=${Status}', name],
               'dnf': ['rpm', '-q', name], 'pacman': ['pacman', '-Q', name]}[manager]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.returncode == 0 and (manager != 'apt-get' or result.stdout == 'install ok installed')


def config_files(machine, home, config):
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    files = {}
    if shell == 'fish':
        files[config / 'fish/conf.d/commander-os.fish'] = '''# Managed by Commander-os direct installation.
if status is-interactive
    fish_add_path "$HOME/.local/bin"
    if test -n "$XDG_CONFIG_HOME"
        set -gx STARSHIP_CONFIG "$XDG_CONFIG_HOME/commander-os/starship.toml"
    else
        set -gx STARSHIP_CONFIG "$HOME/.config/commander-os/starship.toml"
    end
    if command -q starship
        starship init fish | source
    end
    if command -q zoxide
        zoxide init fish | source
    end
    if test -r /usr/share/fish/vendor_functions.d/fzf_key_bindings.fish
        source /usr/share/fish/vendor_functions.d/fzf_key_bindings.fish
        fzf_key_bindings
    end
    fish_user_key_bindings
end
'''
    elif shell in ('bash', 'zsh'):
        files[config / f'commander-os/init.{shell}'] = f'''# Managed by Commander-os direct installation.
export PATH="$HOME/.local/bin:$PATH"
export STARSHIP_CONFIG="${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/starship.toml"
alias ll='eza -la'
alias gs='git status'
command -v starship >/dev/null && eval "$(starship init {shell})"
command -v zoxide >/dev/null && eval "$(zoxide init {shell})"
'''
        files[config / f'commander-os/init.{shell}'] += f'''for commander_fzf in /usr/share/doc/fzf/examples/key-bindings.{shell} /usr/share/fzf/key-bindings.{shell}; do
    if [ -r "$commander_fzf" ]; then . "$commander_fzf"; break; fi
done
unset commander_fzf
'''
        shell_source = Path(__file__).resolve().parents[1] / 'modules/shell'
        extension = 'bash.sh' if shell == 'bash' else 'zsh.zsh'
        for name in ['common.sh', extension]:
            files[config / 'commander-os/shell' / name] = (shell_source / name).read_text()
            files[config / f'commander-os/init.{shell}'] += f'\n. "${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/shell/{name}"\n'
        if shell == 'bash':
            for name in ['ble-start.sh', 'ble-finish.sh']:
                files[config / 'commander-os/shell' / name] = (shell_source / name).read_text()
            init = config / 'commander-os/init.bash'
            # ble.sh provides fzf integration; avoid loading distro bindings twice.
            text = files[init]
            start = text.index('for commander_fzf')
            end = text.index('unset commander_fzf', start) + len('unset commander_fzf')
            text = text[:start] + text[end:]
            prefix = '. "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/shell/ble-start.sh"\n'
            suffix = '\n. "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/shell/ble-finish.sh"\n'
            files[init] = prefix + text + suffix
        startup = home / ('.bashrc' if shell == 'bash' else '.zshrc')
        original = startup.read_text() if startup.exists() else ''
        marker = '# Commander-os shell integration'
        if marker not in original:
            snippet = f'\n{marker}\n[ -r "${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/init.{shell}" ] && . "${{XDG_CONFIG_HOME:-$HOME/.config}}/commander-os/init.{shell}"\n'
            files[startup] = original + snippet
    if shell == 'fish':
        fish_source = Path(__file__).resolve().parents[1] / 'modules/fish'
        for source in fish_source.rglob('*.fish'):
            files[config / 'fish' / source.relative_to(fish_source)] = source.read_text()
        files[home / '.local/bin/fzf-preview'] = (fish_source.parent / 'fzf-preview').read_text()
    if shell != 'keep':
        files[home / '.local/bin/fzf-preview'] = (Path(__file__).resolve().parents[1] / 'modules/fzf-preview').read_text()
        files[config / 'commander-os/starship.toml'] = (Path(__file__).resolve().parents[1] / 'modules/starship.toml').read_text()
    if machine['features']['neovim']:
        # Do not replace an existing editor configuration in direct mode.
        init = config / 'nvim/init.lua'
        record = install_state.load()['files'].get(str(init))
        owned = record and (not init.exists() or (init.is_file() and not init.is_symlink() and install_state.digest(init) == record['installed']))
        if not (config / 'nvim').exists() or owned:
            files[config / 'nvim/init.lua'] = 'vim.opt.number = true\nvim.opt.expandtab = true\nvim.opt.shiftwidth = 2\nvim.opt.tabstop = 2\n'
    return files


def write_configs(files, receipt=None):
    suffix = f'.commander-os-{time.time_ns()}'
    for target in files:
        if target.is_symlink() or str(target.resolve()).startswith('/nix/store/'):
            raise RuntimeError(f'Refusing to replace managed/symlinked configuration: {target}. Use its existing manager.')
    for target, contents in files.items():
        if receipt is not None:
            install_state.capture(receipt, target, contents)
            install_state.save(receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text() == contents:
                continue
            backup = target.with_name(target.name + suffix)
            shutil.copy2(target, backup)
            print(f'Backup: {backup}')
        with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as tmp:
            tmp.write(contents)
        os.replace(tmp.name, target)


def install_native(machine, *, apply, install_missing, configure_login):
    home = Path(machine['homeDirectory'])
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(home / '.config')))
    manager = next((name for name in ('apt-get', 'dnf', 'pacman') if shutil.which(name)), None)
    if not manager:
        raise RuntimeError('Direct installation currently supports apt, dnf and pacman')
    profiles = [Path(os.environ.get('XDG_STATE_HOME', str(home / '.local/state'))) / 'nix/profiles/home-manager',
                Path('/nix/var/nix/profiles/per-user') / machine['username'] / 'home-manager']
    if any(p.exists() for p in profiles):
        raise RuntimeError('An existing Home Manager profile was found. Use Home Manager mode, or test direct mode in a separate account/VM.')
    packages = package_plan(machine, manager)
    files = config_files(machine, home, config)
    # Refuse managed files before any package installation.
    for target in files:
        if target.is_symlink() or str(target.resolve()).startswith('/nix/store/'):
            raise RuntimeError(f'Configuration is already managed: {target}')
    starship = not shutil.which('starship') and not os.access(home / '.local/bin/starship', os.X_OK)
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    starship = starship and shell != 'keep'
    blesh = shell == 'bash' and not (home / '.local/share/blesh/ble.sh').is_file()
    print(f'Direct install via {manager}; Nix and Home Manager will not be installed.')
    print('Missing packages: ' + (', '.join(packages) or 'none'))
    if blesh:
        print('ble.sh will be built from https://github.com/akinomyoga/ble.sh into ~/.local/share/blesh.')
    if starship:
        print('Starship will be installed from https://starship.rs/install.sh into ~/.local/bin.')
    if machine['features']['development']:
        print('Direct development mode installs Git. Lazygit is currently available in Home Manager mode only.')
    print('Configuration files:\n' + '\n'.join(str(p) for p in files))
    if not apply:
        print('Preview only. Rerun with --apply to install.')
        return 0
    if home != Path.home() or machine['username'] != pwd.getpwuid(os.getuid()).pw_name:
        raise ValueError('Activation settings must match the current user and home directory')
    if not install_missing and (packages or starship or blesh):
        raise RuntimeError('Dependencies are missing and --no-install was specified')
    if input('Type APPLY to install the listed tools and configuration: ') != 'APPLY':
        print('Cancelled.')
        return 0
    receipt = install_state.load()
    if receipt.get('backend') not in (None, 'native', 'removed'):
        raise RuntimeError('Use uninstall.sh to remove the recorded Home Manager or detached setup first.')
    receipt.update(backend='native', machine=machine, manager=manager)
    if packages:
        if manager == 'apt-get':
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            command = ['sudo', manager, 'install', '-y']
        elif manager == 'dnf':
            command = ['sudo', manager, 'install', '-y']
        else:
            command = ['sudo', manager, '-S', '--needed', '--noconfirm']
        absent = [name for name in packages if not package_installed(manager, name)]
        install_state.save(receipt)
        try:
            subprocess.run(command + packages, check=True)
        finally:
            # A package transaction can fail after installing some requested packages.
            installed = [name for name in absent if package_installed(manager, name)]
            receipt['packages'] = sorted(set(receipt['packages'] + installed))
            install_state.save(receipt)
    if starship:
        binary = home / '.local/bin/starship'
        install_state.capture(receipt, binary)
        install_state.save(receipt)
        with tempfile.TemporaryDirectory(prefix='commander-os-starship-') as directory:
            script = Path(directory) / 'install.sh'
            subprocess.run(['curl', '--fail', '--show-error', '--location', '--proto', '=https',
                            '--proto-redir', '=https', 'https://starship.rs/install.sh', '-o', str(script)], check=True)
            binary_dir = home / '.local/bin'
            binary_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(['sh', str(script), '--yes', '--bin-dir', str(binary_dir)], check=True)
        install_state.finished(receipt, binary)
    if blesh:
        ble_dir = home / '.local/share/blesh'
        for path in ble_dir.rglob('*'):
            if path.is_file():
                install_state.capture(receipt, path)
        install_state.save(receipt)
        with tempfile.TemporaryDirectory(prefix='commander-os-blesh-') as directory:
            source = Path(directory) / 'ble.sh'
            subprocess.run(['git', 'clone', '--recursive', '--depth', '1', '--shallow-submodules',
                            'https://github.com/akinomyoga/ble.sh.git', str(source)], check=True)
            subprocess.run(['make', '-C', str(source), 'install', f'PREFIX={home / ".local"}'], check=True)
        for path in ble_dir.rglob('*'):
            if path.is_file() and not path.is_symlink():
                receipt['files'].setdefault(str(path), {'original': None, 'mode': None, 'installed': None})
                receipt['files'][str(path)]['installed'] = install_state.digest(path)
        install_state.save(receipt)
    write_configs(files, receipt)
    if shell != 'keep':
        (home / '.local/bin/fzf-preview').chmod(0o700)
    install_state.save(receipt)
    configure_login(machine, native=True)
    print('Direct installation complete. Existing Neovim configuration was preserved if present.')
    return 0

"""Direct installation without Nix or Home Manager."""
import os
import hashlib
import re
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
import time
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import install_state
import host
import fonts


def package_plan(machine, manager):
    if manager == 'brew':
        return brew_package_plan(machine)
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    tools = {'rg': 'ripgrep', 'fd': 'fd-find' if manager == 'apt-get' else 'fd-find' if manager == 'dnf' else 'fd',
             'bat': 'bat', 'eza': 'eza', 'jq': 'jq', 'fzf': 'fzf', 'zoxide': 'zoxide', 'curl': 'curl', 'tar': 'tar'}
    if shell != 'keep':
        tools[shell] = shell
    if shell != 'keep':
        tools.update({'file': 'file', 'trash': 'trash-cli', 'unzip': 'unzip', 'chafa': 'chafa', 'git': 'git', 'fastfetch': 'fastfetch', 'fc-list': 'fontconfig', 'fc-cache': 'fontconfig'})
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
    if manager == 'brew':
        kind = '--cask' if name == MAC_FONT else '--formula'
        result = subprocess.run(['brew', 'list', kind, '--versions', name], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return result.returncode == 0 and bool(result.stdout.strip())
    command = {'apt-get': ['dpkg-query', '-W', '-f=${Status}', name],
               'dnf': ['rpm', '-q', name], 'pacman': ['pacman', '-Q', name]}[manager]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return result.returncode == 0 and (manager != 'apt-get' or result.stdout == 'install ok installed')


# Official release checksums: https://github.com/fastfetch-cli/fastfetch/releases/tag/2.68.1
FASTFETCH_RELEASE = '2.68.1'
FASTFETCH_DEBS = {
    'amd64': ('amd64', '33b046a620b4f15fb6d0f9b3ef2491e6147ae15e40d699a6eef13555634a1b28'),
    'arm64': ('aarch64', '0290a96bf225e0142a2e21238be9ef36c63c959c489f2f3ba6b4c72b5a767b9a'),
}


def apt_has_fastfetch():
    result = subprocess.run(['apt-cache', 'policy', 'fastfetch'], check=True, text=True,
                            stdout=subprocess.PIPE, env=dict(os.environ, LC_ALL='C'))
    candidate = re.search(r'^\s*Candidate:\s*(\S+)', result.stdout, re.MULTILINE)
    return bool(candidate and candidate.group(1) != '(none)')


def install_fastfetch_deb():
    architecture = subprocess.run(['dpkg', '--print-architecture'], check=True, text=True,
                                  stdout=subprocess.PIPE).stdout.strip()
    if architecture not in FASTFETCH_DEBS:
        raise RuntimeError(f'Fastfetch upstream fallback does not support Debian architecture: {architecture}')
    asset_arch, checksum = FASTFETCH_DEBS[architecture]
    name = f'fastfetch-linux-{asset_arch}.deb'
    url = f'https://github.com/fastfetch-cli/fastfetch/releases/download/{FASTFETCH_RELEASE}/{name}'
    with tempfile.TemporaryDirectory(prefix='commander-fastfetch-') as directory:
        package = Path(directory) / name
        subprocess.run(['curl', '--fail', '--show-error', '--location', '--proto', '=https',
                        '--proto-redir', '=https', url, '-o', str(package)], check=True)
        if hashlib.sha256(package.read_bytes()).hexdigest() != checksum:
            raise RuntimeError('Fastfetch package checksum mismatch; package was not installed')
        # Allow apt's unprivileged download user to read this public package.
        Path(directory).chmod(0o755)
        package.chmod(0o644)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', str(package)], check=True)


MAC_FONT = 'font-jetbrains-mono-nerd-font'


def brew_package_plan(machine):
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    tools = {'rg': 'ripgrep', 'fd': 'fd', 'bat': 'bat', 'eza': 'eza', 'jq': 'jq',
             'fzf': 'fzf', 'zoxide': 'zoxide', 'curl': 'curl', 'gtar': 'gnu-tar', 'unxz': 'xz'}
    required = set()
    if shell != 'keep':
        tools.update({'fastfetch': 'fastfetch', 'file': 'file', 'unzip': 'unzip', 'chafa': 'chafa',
                      'git': 'git', 'greadlink': 'coreutils', 'broot': 'broot', 'pdftotext': 'poppler', '7zz': 'sevenzip'})
        # Always use current Homebrew shells, especially instead of Apple's Bash 3.2.
        required.update([shell, 'trash-cli'])
        fonts = [Path.home() / 'Library/Fonts', Path('/Library/Fonts')]
        if not any(list(directory.glob('*JetBrains*Mono*Nerd*.*tf')) for directory in fonts):
            required.add(MAC_FONT)
    if shell == 'bash' and not (Path(machine['homeDirectory']) / '.local/share/blesh/ble.sh').is_file():
        tools.update({'git': 'git', 'gmake': 'make', 'gawk': 'gawk'})
    if shell == 'zsh':
        required.update(['zsh-autosuggestions', 'zsh-syntax-highlighting'])
    if shell != 'keep':
        tools['starship'] = 'starship'
    if machine['features']['neovim']:
        tools['nvim'] = 'neovim'
    if machine['features']['development']:
        tools.update({'git': 'git', 'lazygit': 'lazygit'})
    required.update(package for tool, package in tools.items() if not shutil.which(tool))
    return sorted(name for name in required if not package_installed('brew', name))


def brew_install(packages):
    formulae = [name for name in packages if name != MAC_FONT]
    if formulae:
        subprocess.run(['brew', 'install', '--formula', *formulae], check=True)
    if MAC_FONT in packages:
        subprocess.run(['brew', 'install', '--cask', MAC_FONT], check=True)


def brew_uninstall(packages):
    # Never remove Homebrew itself or unrelated dependencies as a side effect.
    env = dict(os.environ, HOMEBREW_NO_AUTOREMOVE='1', HOMEBREW_NO_INSTALL_CLEANUP='1')
    formulae = [name for name in packages if name != MAC_FONT]
    if formulae:
        subprocess.run(['brew', 'uninstall', '--formula', *formulae], env=env, check=True)
    if MAC_FONT in packages:
        subprocess.run(['brew', 'uninstall', '--cask', MAC_FONT], env=env, check=True)


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
        if host.is_macos() and shell == 'zsh':
            files[config / f'commander-os/init.{shell}'] += 'command -v fzf >/dev/null && source <(fzf --zsh)\n'
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
        if host.is_macos():
            files[config / 'commander-os/shell/macos.sh'] = (shell_source / 'macos.sh').read_text()
            init = config / f'commander-os/init.{shell}'
            files[init] = '. "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/shell/macos.sh"\n' + files[init]
            if shell == 'zsh':
                files[init] += '''
ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=244'
for commander_plugin in "$HOMEBREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh" "$HOMEBREW_PREFIX/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"; do
    [[ -r "$commander_plugin" ]] && source "$commander_plugin"
done
unset commander_plugin
'''
            if shell == 'bash':
                profile = home / '.bash_profile'
                text = profile.read_text() if profile.exists() else ''
                if not profile.exists():
                    # Creating .bash_profile must preserve Bash's previous login fallback.
                    for name in ('.bash_login', '.profile'):
                        if (home / name).is_file():
                            text = f'[ -r "$HOME/{name}" ] && . "$HOME/{name}"\n'
                            break
                if '.bashrc' not in text:
                    files[profile] = text + '\n# Commander-os Bash login integration\n[ -r "$HOME/.bashrc" ] && . "$HOME/.bashrc"\n'
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
        files[config / 'commander-os/greeting.txt'] = machine.get('greeting', 'Hello, {user} ⚡').replace('{user}', machine['username']) + '\n'
        files[config / 'fastfetch/config.jsonc'] = (Path(__file__).resolve().parents[1] / 'modules/fastfetch.jsonc').read_text()
    if host.is_macos() and shell == 'fish':
        target = config / 'fish/conf.d/commander-os.fish'
        files[target] = files[target].replace('    fish_user_key_bindings', '    if command -q fzf\n        fzf --fish | source\n    end\n    fish_user_key_bindings')
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
    manager = ('brew' if shutil.which('brew') else None) if host.is_macos() else next((name for name in ('apt-get', 'dnf', 'pacman') if shutil.which(name)), None)
    if not manager:
        raise RuntimeError('Direct installation requires Homebrew on macOS, or apt, dnf or pacman on Linux')
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
    starship = manager != 'brew' and not shutil.which('starship') and not os.access(home / '.local/bin/starship', os.X_OK)
    shell = machine.get('shell', 'fish' if machine['features']['fish'] else 'keep')
    starship = starship and shell != 'keep'
    font_missing = manager != 'brew' and shell != 'keep' and fonts.needed()
    blesh = shell == 'bash' and not (home / '.local/share/blesh/ble.sh').is_file()
    print(f'Direct install via {manager}; Nix and Home Manager will not be installed.')
    print('Missing packages: ' + (', '.join(packages) or 'none'))
    if manager == 'apt-get' and 'fastfetch' in packages:
        print(f'Fastfetch uses apt when available; otherwise its official {FASTFETCH_RELEASE} .deb is downloaded and checksum-verified.')
    if font_missing:
        print(f'JetBrainsMono Nerd Font {fonts.VERSION} will be downloaded, checksum-verified and installed in your user fonts directory.')
    if blesh:
        print('ble.sh will be built from https://github.com/akinomyoga/ble.sh into ~/.local/share/blesh.')
    if starship:
        print('Starship will be installed from https://starship.rs/install.sh into ~/.local/bin.')
    if machine['features']['development'] and manager != 'brew':
        print('Direct development mode installs Git. Lazygit is currently available in Home Manager mode only.')
    print('Configuration files:\n' + '\n'.join(str(p) for p in files))
    if not apply:
        print('Preview only. Rerun with --apply to install.')
        return 0
    if home != Path.home() or machine['username'] != pwd.getpwuid(os.getuid()).pw_name:
        raise ValueError('Activation settings must match the current user and home directory')
    if not install_missing and (packages or starship or blesh or font_missing):
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
        elif manager == 'brew':
            command = ['brew', 'install', '--formula']
        elif manager == 'dnf':
            command = ['sudo', manager, 'install', '-y']
        else:
            command = ['sudo', manager, '-S', '--needed', '--noconfirm']
        absent = [name for name in packages if not package_installed(manager, name)]
        install_state.save(receipt)
        try:
            fallback = manager == 'apt-get' and 'fastfetch' in packages and not apt_has_fastfetch()
            distro_packages = [p for p in packages if not (fallback and p == 'fastfetch')]
            if distro_packages:
                if manager == 'brew':
                    brew_install(distro_packages)
                else:
                    subprocess.run(command + distro_packages, check=True)
            if fallback:
                install_fastfetch_deb()
        finally:
            # A package transaction can fail after installing some requested packages.
            installed = [name for name in absent if package_installed(manager, name)]
            receipt['packages'] = sorted(set(receipt['packages'] + installed))
            install_state.save(receipt)
    if font_missing:
        fonts.install(home, receipt)
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
            subprocess.run(['gmake' if manager == 'brew' else 'make', '-C', str(source), 'install', f'PREFIX={home / ".local"}'], check=True)
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
    if shell != 'keep':
        print('Select JetBrainsMono Nerd Font Mono in your terminal profile, then close all terminal windows and reopen them.')
    print('Direct installation complete. Existing Neovim configuration was preserved if present.')
    return 0

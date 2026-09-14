"""Host/platform details shared by installation and maintenance."""
from pathlib import Path
import platform
import subprocess


def is_macos():
    return platform.system() == 'Darwin'


def system():
    architecture = {'arm64': 'aarch64', 'AMD64': 'x86_64'}.get(platform.machine(), platform.machine())
    return architecture + ('-darwin' if is_macos() else '-linux')


def brew_prefix():
    result = subprocess.run(['brew', '--prefix'], check=True, text=True, stdout=subprocess.PIPE)
    prefix = Path(result.stdout.strip())
    if not prefix.is_absolute() or '..' in prefix.parts:
        raise RuntimeError('Homebrew returned an invalid installation prefix')
    return prefix


def native_shell_paths(shell):
    if is_macos():
        prefix = brew_prefix()
        return [prefix / 'bin' / shell, prefix / 'opt' / shell / 'bin' / shell]
    return [Path('/usr/bin') / shell, Path('/bin') / shell]


def fallback_shell():
    return '/bin/zsh' if is_macos() else '/bin/bash'

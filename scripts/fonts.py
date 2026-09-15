"""User-local Nerd Font installation for native Linux shells."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

import install_state

VERSION = '3.4.0'
URL = f'https://github.com/ryanoasis/nerd-fonts/releases/download/v{VERSION}/JetBrainsMono.tar.xz'
# Upstream release SHA-256.txt.
SHA256 = 'ef552a3e638f25125c6ad4c51176a6adcdce295ab1d2ffacf0db060caf8c1582'
FAMILY = 'JetBrainsMono Nerd Font Mono'
FILES = [f'JetBrainsMonoNerdFontMono-{style}.ttf' for style in ('Regular', 'Bold', 'Italic', 'BoldItalic')] + ['OFL.txt']


def needed():
    if not shutil.which('fc-list'):
        return True
    result = subprocess.run(['fc-list', '--format=%{family}\n'], check=True, text=True, stdout=subprocess.PIPE)
    return FAMILY not in {name.strip() for line in result.stdout.splitlines() for name in line.split(',')}


def install(home, receipt):
    directory = Path(os.environ.get('XDG_DATA_HOME', str(home / '.local/share'))) / 'fonts/commander-os'
    if not directory.is_absolute() or '..' in directory.parts or not directory.is_relative_to(home):
        raise RuntimeError('Font installation requires XDG_DATA_HOME inside your home directory')
    if any(path.is_symlink() for path in [directory, *directory.parents] if path.is_relative_to(home)):
        raise RuntimeError('Refusing a symlinked font installation directory')
    with tempfile.TemporaryDirectory(prefix='commander-font-') as tmp:
        archive = Path(tmp) / 'JetBrainsMono.tar.xz'
        subprocess.run(['curl', '--fail', '--show-error', '--location', '--proto', '=https',
                        '--proto-redir', '=https', URL, '-o', str(archive)], check=True)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError('Nerd Font checksum mismatch; no fonts installed')
        with tarfile.open(archive, 'r:xz') as source:
            # Read only explicitly named regular files; never extract archive paths.
            contents = {}
            for name in FILES:
                entry = source.getmember(name)
                if not entry.isfile():
                    raise RuntimeError(f'Invalid font archive entry: {name}')
                contents[name] = source.extractfile(entry).read()
        for name in contents:
            if (directory / name).is_symlink():
                raise RuntimeError('Refusing to overwrite a symlinked font')
        directory.mkdir(parents=True, exist_ok=True)
        for name, data in contents.items():
            target = directory / name
            install_state.capture(receipt, target)
            receipt['files'][str(target)]['installed'] = hashlib.sha256(data).hexdigest()
            install_state.save(receipt)
            with tempfile.NamedTemporaryFile(dir=directory, delete=False) as staged:
                staged.write(data)
            os.replace(staged.name, target)
            target.chmod(0o644)
    subprocess.run(['fc-cache', '-f', str(directory)], check=True)

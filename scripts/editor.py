"""LazyVim starter ownership and verified native Linux tool fallbacks."""
import hashlib
import gzip
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile

import host
import install_state

SOURCE = Path(__file__).resolve().parents[1] / 'modules/neovim'
NVIM_VERSION = '0.11.6'
TREE_VERSION = '0.26.1'
ASSETS = {
    'x86_64-linux': ('x86_64', 'x64', '2fc90b962327f73a78afbfb8203fd19db8db9cdf4ee5e2bef84704339add89cc', 'd74182fffbf441f247371ad6af77d99b10ac9f788d7e068e4b44992d9d6d7c26'),
    'aarch64-linux': ('arm64', 'arm64', '8ddc0c101846145e830b17bbca50782ca9307eee4fab539d9e2ddaf8793c06f1', '98a710e8ab9d502c50b02acd32d553c5fb5d00285cd458e5907af8a580c5a4ea'),
}


def config_files(config):
    root = config / 'nvim'
    records = install_state.load()['files']
    init = root / 'init.lua'
    record = records.get(str(init))
    owned = record and (not init.exists() or (init.is_file() and not init.is_symlink() and install_state.digest(init) == record['installed']))
    if root.is_symlink() or (root.exists() and not owned):
        return {}
    files = {root / p.relative_to(SOURCE): p.read_text() for p in SOURCE.rglob('*') if p.is_file()}
    # Preserve the whole existing editor if any starter file was customized or is unowned.
    for path in files:
        if any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root)):
            return {}
        if path.exists():
            entry = records.get(str(path))
            if not path.is_file() or not entry or install_state.digest(path) != entry['installed']:
                return {}
    return files


def executable(name, home):
    local = home / '.local/bin' / name
    return str(local) if os.access(local, os.X_OK) else shutil.which(name)


def recent(name, minimum, home):
    path = executable(name, home)
    if not path:
        return False
    try:
        result = subprocess.run([path, '--version'], text=True, capture_output=True)
    except OSError:
        return False
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', result.stdout)
    return result.returncode == 0 and bool(match) and tuple(map(int, match.groups())) >= minimum


def needs_tools(home):
    return not recent('nvim', (0, 11, 2), home) or not recent('tree-sitter', (0, 26, 1), home)


def download(url, checksum, target):
    subprocess.run(['curl', '--fail', '--show-error', '--location', '--proto', '=https', '--proto-redir', '=https', url, '-o', str(target)], check=True)
    if hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
        raise RuntimeError('Editor download checksum mismatch; refusing to install')


def write_tools(home, files, receipt):
    for path, (data, mode) in files.items():
        if not path.is_relative_to(home) or '..' in path.parts or any(p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(home)):
            raise RuntimeError(f'Refusing unsafe editor path: {path}')
        # Preserve pre-existing tools instead of shadowing or replacing them silently.
        entry = receipt['files'].get(str(path))
        if path.exists() and (not entry or install_state.digest(path) != entry['installed']):
            raise RuntimeError(f'Existing custom editor tool needs manual upgrade: {path}')
        install_state.capture(receipt, path)
        receipt['files'][str(path)]['installed'] = hashlib.sha256(data).hexdigest()
    install_state.save(receipt)
    for path, (data, mode) in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as staged:
            staged.write(data)
        os.chmod(staged.name, mode)
        os.replace(staged.name, path)


def ensure_tools(home, receipt):
    missing_nvim = not recent('nvim', (0, 11, 2), home)
    missing_tree = not recent('tree-sitter', (0, 26, 1), home)
    if missing_nvim or missing_tree:
        if host.is_macos():
            raise RuntimeError('LazyVim needs Neovim >= 0.11.2 and tree-sitter >= 0.26.1. Run brew upgrade neovim tree-sitter-cli, then rerun the installer.')
        system = host.system()
        if system not in ASSETS:
            raise RuntimeError(f'No verified editor fallback for {system}; install current Neovim and tree-sitter first')
        nvim_arch, tree_arch, nvim_sha, tree_sha = ASSETS[system]
        with tempfile.TemporaryDirectory(prefix='myfish-editor-') as tmp:
            files = {}
            if missing_nvim:
                archive = Path(tmp) / 'nvim.tar.gz'
                name = f'nvim-linux-{nvim_arch}'
                download(f'https://github.com/neovim/neovim/releases/download/v{NVIM_VERSION}/{name}.tar.gz', nvim_sha, archive)
                root = home / '.local/share/commander-os/nvim' / NVIM_VERSION
                with tarfile.open(archive, 'r:gz') as source:
                    for entry in source:
                        path = Path(entry.name)
                        if path.is_absolute() or '..' in path.parts or path.parts[0] != name:
                            raise RuntimeError('Invalid Neovim archive path')
                        if entry.isdir():
                            continue
                        if not entry.isfile():
                            raise RuntimeError('Unsupported Neovim archive entry')
                        files[root / Path(*path.parts[1:])] = (source.extractfile(entry).read(), 0o755 if entry.mode & 0o111 else 0o644)
                binary = root / 'bin/nvim'
                wrapper = '#!/bin/sh\nexec ' + shlex.quote(str(binary)) + ' "$@"\n'
                files[home / '.local/bin/nvim'] = (wrapper.encode(), 0o755)
            if missing_tree:
                archive = Path(tmp) / 'tree-sitter.gz'
                download(f'https://github.com/tree-sitter/tree-sitter/releases/download/v{TREE_VERSION}/tree-sitter-linux-{tree_arch}.gz', tree_sha, archive)
                files[home / '.local/bin/tree-sitter'] = (gzip.decompress(archive.read_bytes()), 0o755)
            write_tools(home, files, receipt)
    if needs_tools(home):
        raise RuntimeError('Editor tools could not run on this system; LazyVim configuration was not applied')
    probe = subprocess.run([executable('nvim', home), '--headless', '-u', 'NONE', '-i', 'NONE', '+lua if not jit then vim.cmd("cquit") end', '+qa'], capture_output=True, text=True)
    if probe.returncode:
        raise RuntimeError('LazyVim requires a working LuaJIT build of Neovim')

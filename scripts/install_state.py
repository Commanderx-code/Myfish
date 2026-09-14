"""Private installation records used for conservative removal and recovery."""
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile


def directory():
    return Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'commander-os'


def load():
    path = directory() / 'installation.json'
    data = json.loads(path.read_text()) if path.exists() else {'version': 1, 'files': {}, 'packages': []}
    if data.get('version') != 1 or not isinstance(data.get('files'), dict) or not isinstance(data.get('packages'), list):
        raise ValueError('Invalid Commander-os installation record')
    return data


def save(data):
    directory().mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(mode='w', dir=directory(), delete=False) as target:
        json.dump(data, target, indent=2)
        target.write('\n')
    os.replace(target.name, directory() / 'installation.json')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(data, path, contents=None):
    if path.is_symlink():
        raise RuntimeError(f'Refusing to record ownership of a symlink: {path}')
    if str(path) not in data['files']:
        data['files'][str(path)] = {
            'original': base64.b64encode(path.read_bytes()).decode() if path.is_file() else None,
            'mode': path.stat().st_mode & 0o777 if path.is_file() else None,
            'installed': None,
        }
    if contents is not None:
        # Journal the intended content before writing, including partially failed installs.
        data['files'][str(path)]['installed'] = hashlib.sha256(contents.encode()).hexdigest()


def finished(data, path):
    data['files'][str(path)]['installed'] = digest(path)
    save(data)

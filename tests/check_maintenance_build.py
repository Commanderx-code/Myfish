"""Build maintenance environments and check retained tools without activation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import bootstrap
import lifecycle

machine = json.loads((ROOT / 'machine.example.json').read_text())
machine['shell'] = 'zsh'
with tempfile.TemporaryDirectory(prefix='commander-build-check-') as temp:
    source = Path(temp) / 'home'
    source.mkdir()
    bootstrap.stage(source, machine)
    result = subprocess.run(['nix', '--extra-experimental-features', 'nix-command flakes', 'build',
                             '--no-link', '--print-out-paths',
                             f'path:{source}#homeConfigurations.commander.activationPackage'],
                            check=True, text=True, stdout=subprocess.PIPE)
    active = Path(result.stdout.strip())
    plan = Path(temp) / 'maintenance'
    plan.mkdir()
    removal, retained = lifecycle.build_hm(machine, active, True, plan)
    assert (removal / 'activate').is_file()
    expected = {p.name for p in (active / 'home-path/bin').iterdir()} - {'home-manager'}
    actual = {p.name for p in (retained / 'bin').iterdir()}
    assert actual == expected, f'Missing: {expected - actual}; unexpected: {actual - expected}'
    assert all((retained / 'bin' / name).exists() for name in expected)
    subprocess.run([str(retained / 'bin/zsh'), '-f', '-c', 'exit 0'], check=True)
    for command in ('bat', 'gzip', 'broot', 'fastfetch', 'starship'):
        subprocess.run([str(retained / 'bin' / command), '--version'], check=True, stdout=subprocess.DEVNULL)
print('Maintenance builds verified: all tool entries preserved except Home Manager; no activation performed.')

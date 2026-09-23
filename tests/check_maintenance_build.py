"""Build maintenance environments and check retained tools without activation."""
import json
import os
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
machine['system'] = lifecycle.host.system()
if lifecycle.host.is_macos():
    machine['homeDirectory'] = '/Users/example'
with tempfile.TemporaryDirectory(prefix='commander-build-check-') as temp:
    # Fish is covered by flake check; build Bash too so ble.sh is checked on Macs.
    bash_source = Path(temp) / 'bash-home'
    bash_source.mkdir()
    bootstrap.stage(bash_source, dict(machine, shell='bash'))
    subprocess.run(['nix', '--extra-experimental-features', 'nix-command flakes', 'build',
                    '--no-link', f'path:{bash_source}#homeConfigurations.commander.activationPackage'], check=True)
    source = Path(temp) / 'home'
    source.mkdir()
    bootstrap.stage(source, machine)
    result = subprocess.run(['nix', '--extra-experimental-features', 'nix-command flakes', 'build',
                             '--no-link', '--print-out-paths',
                             f'path:{source}#homeConfigurations.commander.activationPackage'],
                            check=True, text=True, stdout=subprocess.PIPE)
    active = Path(result.stdout.strip())
    recovery_root = Path(temp) / 'recovery-root'
    subprocess.run([lifecycle.nix_tool('nix-store'), '--realise', str(active),
                    '--add-root', str(recovery_root)], check=True, stdout=subprocess.DEVNULL)
    assert recovery_root.resolve() == active
    subprocess.run([lifecycle.nix_tool('nix-env'), '--version'], check=True, stdout=subprocess.DEVNULL)
    plan = Path(temp) / 'maintenance'
    plan.mkdir()
    removal, retained = lifecycle.build_hm(machine, active, True, plan)
    assert (removal / 'activate').is_file()
    assert 'require("config.lazy")' in (active / 'home-files/.config/nvim/init.lua').read_text()
    picker = active / 'home-files/.local/bin/fzf-rg'
    assert picker.read_bytes() == (ROOT / 'modules/fzf-rg').read_bytes()
    assert picker.stat().st_mode & 0o111
    assert (active / 'home-files/.config/nvim/lua/config/lazy.lua').read_bytes() == (ROOT / 'modules/neovim/lua/config/lazy.lua').read_bytes()
    editor_home = Path(temp) / 'editor-check'
    editor_home.mkdir()
    editor_env = dict(os.environ, HOME=str(editor_home), XDG_CONFIG_HOME=str(editor_home / 'config'),
                      XDG_DATA_HOME=str(editor_home / 'data'), XDG_STATE_HOME=str(editor_home / 'state'),
                      XDG_CACHE_HOME=str(editor_home / 'cache'), MYFISH_STARTER=str(ROOT / 'modules/neovim'))
    check_lua = "lua assert(jit); for _, tool in ipairs({'git', 'curl', 'tree-sitter', 'cc'}) do assert(vim.fn.executable(tool) == 1, tool) end; for _, file in ipairs(vim.fn.glob(vim.env.MYFISH_STARTER .. '/**/*.lua', false, true)) do assert(loadfile(file)) end"
    subprocess.run([str(retained / 'bin/nvim'), '--headless', '-u', 'NONE', '-i', 'NONE',
                    '-c', check_lua, '-c', 'qa'], check=True, env=editor_env)

    fastfetch_config = active / 'home-files/.config/fastfetch/config.jsonc'
    assert fastfetch_config.read_bytes() == (ROOT / 'modules/fastfetch.jsonc').read_bytes()
    subprocess.run([str(retained / 'bin/fastfetch'), '--config', str(fastfetch_config), '--pipe'],
                   check=True, stdout=subprocess.DEVNULL)
    expected = {p.name for p in (active / 'home-path/bin').iterdir()} - {'home-manager'}
    actual = {p.name for p in (retained / 'bin').iterdir()}
    assert actual == expected, f'Missing: {expected - actual}; unexpected: {actual - expected}'
    assert all((retained / 'bin' / name).exists() for name in expected)
    subprocess.run([str(retained / 'bin/zsh'), '-f', '-c', 'exit 0'], check=True)
    for command in ('bat', 'gzip', 'broot', 'fastfetch', 'starship'):
        subprocess.run([str(retained / 'bin' / command), '--version'], check=True, stdout=subprocess.DEVNULL)
print('Maintenance builds verified: all tool entries preserved except Home Manager; no activation performed.')

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native', ROOT / 'scripts/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeTests(unittest.TestCase):
    def test_retired_helpers_archive_only_unchanged_installer_created_files(self):
        config = self.home / '.config'
        target = config / 'fish/conf.d/20-icons.fish'
        target.parent.mkdir(parents=True)
        receipt = {'version': 1, 'files': {}, 'packages': []}
        native.install_state.capture(receipt, target, 'old icons')
        target.write_text('old icons')
        native.retire_fish_helpers(config, receipt)
        self.assertFalse(target.exists())
        self.assertNotIn(str(target), receipt['files'])
        self.assertEqual(next(target.parent.glob('*.commander-os-retired-*')).read_text(), 'old icons')
        for kind in ('unrecorded', 'modified', 'preexisting', 'symlink'):
            with self.subTest(kind=kind):
                target.unlink(missing_ok=True)
                target.write_text('personal')
                receipt['files'] = {}
                if kind != 'unrecorded':
                    receipt['files'][str(target)] = {
                        'original': 'saved original' if kind == 'preexisting' else None,
                        'installed': native.install_state.digest(target) if kind != 'modified' else 'old hash',
                    }
                if kind == 'symlink':
                    destination = self.home / 'managed'
                    destination.write_text('personal')
                    target.unlink()
                    target.symlink_to(destination)
                native.retire_fish_helpers(config, receipt)
                self.assertEqual(target.read_text(), 'personal')

    def setUp(self):
        for target, value in [('editor.needs_tools', False), ('editor.ensure_tools', None)]:
            patcher = patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        font_patch = patch('fonts.needed', return_value=False)
        font_patch.start()
        self.addCleanup(font_patch.stop)
        platform_patch = patch.object(native.host, 'is_macos', return_value=False)
        platform_patch.start()
        self.addCleanup(platform_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.machine = json.loads((ROOT / 'machine.example.json').read_text())
        self.machine['homeDirectory'] = str(self.home)
        env = patch.dict(os.environ, XDG_STATE_HOME=str(self.home / '.local/state'), XDG_CONFIG_HOME=str(self.home / '.config'))
        env.start()
        self.addCleanup(env.stop)

    def test_bash_append_preserves_existing_content_and_is_idempotent(self):
        self.machine['shell'] = 'bash'
        rc = self.home / '.bashrc'
        rc.write_text('export MY_SETTING=fixture\n')
        native.write_configs(native.config_files(self.machine, self.home, self.home / '.config'))
        first = rc.read_text()
        self.assertTrue(first.startswith('export MY_SETTING=fixture\n'))
        self.assertEqual(len(list(self.home.glob('.bashrc.commander-os-*'))), 1)
        native.write_configs(native.config_files(self.machine, self.home, self.home / '.config'))
        self.assertEqual(rc.read_text(), first)
        self.assertEqual(len(list(self.home.glob('.bashrc.commander-os-*'))), 1)

    def test_symlinked_files_are_not_overwritten(self):
        target = self.home / 'managed'
        target.write_text('keep')
        link = self.home / '.bashrc'
        link.symlink_to(target)
        with self.assertRaises(RuntimeError):
            native.write_configs({link: 'replace'})
        self.assertEqual(target.read_text(), 'keep')

    def test_existing_neovim_is_preserved(self):
        nvim = self.home / '.config/nvim'
        nvim.mkdir(parents=True)
        self.assertNotIn(nvim / 'init.lua', native.config_files(self.machine, self.home, self.home / '.config'))

    def test_keep_does_not_write_shell_configuration(self):
        self.machine['shell'] = 'keep'
        self.machine['features']['neovim'] = False
        self.assertEqual(native.config_files(self.machine, self.home, self.home / '.config'), {})

    def test_preview_never_installs_or_writes(self):
        with patch.object(native.shutil, 'which', return_value='/fixture'), \
             patch.object(native.subprocess, 'run') as run, \
             patch('builtins.input', side_effect=AssertionError('preview prompted')):
            self.assertEqual(native.install_native(self.machine, apply=False, install_missing=True,
                                                  configure_login=lambda *a, **kw: self.fail('login changed')), 0)
            run.assert_not_called()
        self.assertEqual(list(self.home.iterdir()), [])

    def test_fish_generated_syntax(self):
        self.machine['shell'] = 'fish'
        files = native.config_files(self.machine, self.home, self.home / '.config')
        contents = next(v for k, v in files.items() if k.suffix == '.fish')
        result = subprocess.run(['fish', '--no-config', '--no-execute'], input=contents,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failed_package_install_does_not_write_configuration(self):
        from types import SimpleNamespace
        with patch.object(native.shutil, 'which', side_effect=lambda name: '/usr/bin/apt-get' if name == 'apt-get' else None), \
             patch.object(Path, 'home', return_value=self.home), \
             patch.object(native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='example')), \
             patch('builtins.input', return_value='APPLY'), \
             patch.object(native.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['apt-get'])):
            with self.assertRaises(subprocess.CalledProcessError):
                native.install_native(self.machine, apply=True, install_missing=True,
                                      configure_login=lambda *a, **kw: self.fail('login changed'))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_native_apply_without_missing_tools_never_runs_nix(self):
        from types import SimpleNamespace
        with patch.object(native.shutil, 'which', return_value='/fixture'), \
             patch.object(native.os, 'access', return_value=True), \
             patch.object(Path, 'home', return_value=self.home), \
             patch.object(native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='example')), \
             patch('builtins.input', return_value='APPLY'), \
             patch.object(native.subprocess, 'run') as run:
            calls = []
            self.assertEqual(native.install_native(self.machine, apply=True, install_missing=False,
                configure_login=lambda *a, **kw: calls.append(kw)), 0)
            run.assert_not_called()
            self.assertEqual(calls, [{'native': True}])
        self.assertTrue((self.home / '.config/fish/conf.d/commander-os.fish').is_file())
        picker = self.home / '.local/bin/fzf-rg'
        self.assertEqual(picker.read_bytes(), (ROOT / 'modules/fzf-rg').read_bytes())
        self.assertTrue(os.access(picker, os.X_OK))

    def test_bash_ble_wraps_prompt_and_shell_bindings(self):
        self.machine['shell'] = 'bash'
        files = native.config_files(self.machine, self.home, self.home / '.config')
        init = files[self.home / '.config/commander-os/init.bash']
        self.assertLess(init.index('ble-start.sh'), init.index('starship init bash'))
        self.assertLess(init.index('bash.sh'), init.index('ble-finish.sh'))
        self.assertNotIn('for commander_fzf', init)
        self.assertIn(self.home / '.config/commander-os/shell/ble-start.sh', files)

    def test_bash_preview_does_not_download_ble(self):
        self.machine['shell'] = 'bash'
        self.test_preview_never_installs_or_writes()

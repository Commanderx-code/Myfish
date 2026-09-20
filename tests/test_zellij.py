import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native


class ZellijTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / 'config'
        self.machine = {'username': 'test', 'homeDirectory': str(self.home), 'shell': 'fish',
                        'features': {'fish': True, 'neovim': False, 'development': False}}

    def test_package_plans_include_missing_zellij_for_all_shells(self):
        for shell in ('fish', 'bash', 'zsh', 'keep'):
            self.machine['shell'] = shell
            for manager in ('apt-get', 'dnf', 'pacman', 'brew'):
                with self.subTest(shell=shell, manager=manager), \
                     patch.object(native.shutil, 'which', side_effect=lambda name: None if name == 'zellij' else '/fixture'), \
                     patch.object(native, 'package_installed', return_value=False):
                    self.assertEqual('zellij' in native.package_plan(self.machine, manager), shell != 'keep')

    def test_existing_binary_is_not_reinstalled(self):
        with patch.object(native.shutil, 'which', return_value='/fixture'):
            for manager in ('apt-get', 'dnf', 'pacman', 'brew'):
                self.assertNotIn('zellij', native.package_plan(self.machine, manager))

    def test_new_config_matches_selected_shell_and_is_not_autostarted(self):
        for shell in ('fish', 'bash', 'zsh'):
            self.machine['shell'] = shell
            files = native.config_files(self.machine, self.home, self.config)
            config = files[self.config / 'zellij/config.kdl']
            self.assertIn('default_mode "locked"', config)
            self.assertIn('theme "tokyo-night-storm"', config)
            self.assertIn(f'default_shell {json.dumps(shell)}', config)
            for path, text in files.items():
                if path.suffix in ('.fish', '.bash', '.zsh'):
                    self.assertNotIn('zellij', text)

    def test_existing_config_and_managed_link_are_preserved(self):
        target = self.config / 'zellij/config.kdl'
        target.parent.mkdir(parents=True)
        target.write_text('personal settings')
        self.assertNotIn(target, native.config_files(self.machine, self.home, self.config))
        target.unlink()
        target.symlink_to(self.home / 'missing-managed-target')
        self.assertNotIn(target, native.config_files(self.machine, self.home, self.config))

    def test_apt_package_probe(self):
        for candidate, expected in (('0.44.3', True), ('(none)', False)):
            with patch.object(native.subprocess, 'run', return_value=SimpleNamespace(stdout=f'  Candidate: {candidate}\n')) as run:
                self.assertEqual(native.apt_has_package('zellij'), expected)
                self.assertEqual(run.call_args.args[0], ['apt-cache', 'policy', 'zellij'])

    def test_missing_apt_candidate_stops_before_installing_or_writing(self):
        import os
        with patch.dict(os.environ, XDG_CONFIG_HOME=str(self.config), XDG_STATE_HOME=str(self.home / 'state')), \
             patch.object(native.host, 'is_macos', return_value=False), \
             patch.object(native.shutil, 'which', return_value='/fixture'), \
             patch.object(native, 'package_plan', return_value=['zellij']), \
             patch.object(native, 'apt_has_package', return_value=False), \
             patch.object(native.fonts, 'needed', return_value=False), \
             patch.object(Path, 'home', return_value=self.home), \
             patch.object(native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='test')), \
             patch('builtins.input', return_value='APPLY'), \
             patch.object(native.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'Zellij is unavailable'):
                native.install_native(self.machine, apply=True, install_missing=True,
                                      configure_login=lambda *a, **kw: self.fail('login changed'))
            self.assertEqual(run.call_args_list[0].args[0], ['sudo', 'apt-get', 'update'])
            self.assertEqual(run.call_count, 1)
            self.assertFalse(self.config.exists())

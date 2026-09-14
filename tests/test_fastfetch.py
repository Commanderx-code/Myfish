import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native
import install_state


class FastfetchTests(unittest.TestCase):
    def setUp(self):
        platform_patch = patch.object(native.host, 'is_macos', return_value=False)
        platform_patch.start()
        self.addCleanup(platform_patch.stop)

    def test_missing_fastfetch_is_planned_for_every_shell_and_manager(self):
        with tempfile.TemporaryDirectory() as home:
            for shell in ('fish', 'bash', 'zsh'):
                machine = {'shell': shell, 'homeDirectory': home,
                           'features': {'fish': shell == 'fish', 'neovim': False, 'development': False}}
                for manager in ('apt-get', 'dnf', 'pacman'):
                    with self.subTest(shell=shell, manager=manager), patch.object(native.shutil, 'which', side_effect=lambda name: None if name == 'fastfetch' else '/fixture'):
                        self.assertIn('fastfetch', native.package_plan(machine, manager))
                    with patch.object(native.shutil, 'which', return_value='/fixture'):
                        self.assertNotIn('fastfetch', native.package_plan(machine, manager))

    def test_apt_candidate_detection(self):
        for output, expected in [('fastfetch:\n  Candidate: 2.60.0-1\n', True),
                                 ('fastfetch:\n  Candidate: (none)\n', False), ('', False)]:
            with patch.object(native.subprocess, 'run', return_value=SimpleNamespace(stdout=output)) as run:
                self.assertEqual(native.apt_has_fastfetch(), expected)
                self.assertEqual(run.call_args.kwargs['env']['LC_ALL'], 'C')

    def test_fallback_architecture_mapping_and_verified_install(self):
        for arch, asset in [('amd64', 'amd64'), ('arm64', 'aarch64')]:
            calls = []
            data = b'fixture deb'
            def run(command, **kwargs):
                calls.append(command)
                if command[0] == 'dpkg':
                    return SimpleNamespace(stdout=arch + '\n')
                if command[0] == 'curl':
                    Path(command[-1]).write_bytes(data)
            with patch.object(native.subprocess, 'run', side_effect=run), \
                 patch.dict(native.FASTFETCH_DEBS, {arch: (asset, hashlib.sha256(data).hexdigest())}):
                native.install_fastfetch_deb()
            self.assertIn(f'fastfetch-linux-{asset}.deb', calls[1][-3])
            self.assertEqual(calls[-1][:4], ['sudo', 'apt-get', 'install', '-y'])

    def test_bad_checksum_never_invokes_apt(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            if command[0] == 'dpkg':
                return SimpleNamespace(stdout='amd64\n')
            Path(command[-1]).write_bytes(b'corrupt')
        with patch.object(native.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(RuntimeError, 'checksum mismatch'):
                native.install_fastfetch_deb()
        self.assertFalse(any(c[0] == 'sudo' for c in calls))

    def test_no_install_refuses_missing_fastfetch_without_download(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            machine = {'username': 'example', 'homeDirectory': directory, 'shell': 'keep',
                       'features': {'fish': False, 'neovim': False, 'development': False}}
            with patch.dict(os.environ, XDG_STATE_HOME=directory + '/state'), \
                 patch.object(native, 'package_plan', return_value=['fastfetch']), \
                 patch.object(native.shutil, 'which', return_value='/fixture'), \
                 patch.object(Path, 'home', return_value=home), \
                 patch.object(native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='example')), \
                 patch.object(native.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, '--no-install'):
                    native.install_native(machine, apply=True, install_missing=False, configure_login=lambda *a, **kw: None)
                run.assert_not_called()

    def test_fallback_is_recorded_and_apt_repository_is_preferred(self):
        for available in (True, False):
            with self.subTest(available=available), tempfile.TemporaryDirectory() as directory:
                machine = {'username': 'example', 'homeDirectory': directory, 'shell': 'keep',
                           'features': {'fish': False, 'neovim': False, 'development': False}}
                with patch.dict(os.environ, XDG_STATE_HOME=directory + '/state'), \
                     patch.object(Path, 'home', return_value=Path(directory)), \
                     patch.object(native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='example')), \
                     patch.object(native.shutil, 'which', return_value='/fixture'), \
                     patch.object(native, 'package_plan', return_value=['fastfetch']), \
                     patch.object(native, 'package_installed', side_effect=[False, True]), \
                     patch.object(native, 'apt_has_fastfetch', return_value=available), \
                     patch.object(native, 'install_fastfetch_deb') as fallback, \
                     patch.object(native.subprocess, 'run') as run, patch('builtins.input', return_value='APPLY'):
                    native.install_native(machine, apply=True, install_missing=True, configure_login=lambda *a, **kw: None)
                    self.assertEqual(fallback.call_count, int(not available))
                    if available:
                        self.assertIn(['sudo', 'apt-get', 'install', '-y', 'fastfetch'], [c.args[0] for c in run.call_args_list])
                    self.assertEqual(install_state.load()['packages'], ['fastfetch'])

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).resolve().parents[1] / 'scripts/bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.machine = json.loads((bootstrap.ROOT / 'machine.example.json').read_text())

    def test_private_files_do_not_enter_build_source(self):
        source = self.root / 'checkout'
        source.mkdir()
        for name in ('flake.nix', 'flake.lock', 'machine.example.json'):
            (source / name).write_text('{}')
        (source / 'modules').mkdir()
        (source / '.env').write_text('fixture-secret')
        destination = self.root / 'build'
        destination.mkdir()
        with patch.object(bootstrap, 'ROOT', source):
            bootstrap.stage(destination, self.machine)
        self.assertFalse((destination / '.env').exists())
        self.assertEqual(json.loads((destination / 'machine.json').read_text()), self.machine)

    def test_rejects_unknown_fields_and_invalid_features(self):
        self.machine['password'] = 'fixture'
        with self.assertRaises(ValueError):
            bootstrap.validate(self.machine)
        self.machine.pop('password')
        self.machine['features']['fish'] = 'false'
        with self.assertRaises(ValueError):
            bootstrap.validate(self.machine)

    def run_preview(self, apply=False, answer='cancel'):
        config = self.root / 'machine.json'
        machine = bootstrap.default_machine()
        config.write_text(json.dumps(machine))
        original = config.read_bytes()
        package = self.root / 'package'
        package.mkdir()
        (package / 'activate').touch()
        argv = ['bootstrap', '--config', str(config)] + (['--apply'] if apply else [])
        with patch.object(sys, 'argv', argv), patch.object(bootstrap.os, 'geteuid', return_value=1000), \
             patch.object(bootstrap.shutil, 'which', return_value='/fixture/nix'), \
             patch.object(bootstrap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, str(package))) as run, \
             patch('builtins.input', return_value=answer) as prompt, \
             patch.object(bootstrap, 'configure_shell_login') as login, \
             patch.dict(os.environ, XDG_STATE_HOME=str(self.root / 'state')):
            self.assertEqual(bootstrap.main(), 0)
            self.assertEqual(config.read_bytes(), original)
            self.assertEqual(login.call_count, int(apply and answer == 'APPLY'))
            return run.call_args_list, prompt.call_count

    def test_preview_never_activates_or_prompts(self):
        calls, prompts = self.run_preview()
        self.assertEqual(len(calls), 1)
        self.assertEqual(prompts, 0)

    def test_cancel_does_not_activate(self):
        calls, prompts = self.run_preview(apply=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(prompts, 1)

    def test_confirmed_activation_uses_backup_suffix(self):
        calls, prompts = self.run_preview(apply=True, answer='APPLY')
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1].kwargs['env']['HOME_MANAGER_BACKUP_EXT'].startswith('commander-os-'))

    def test_disabled_fish_never_changes_shell(self):
        self.machine['features']['fish'] = False
        with patch.object(bootstrap.subprocess, 'run') as run:
            bootstrap.configure_shell_login(self.machine)
            run.assert_not_called()

    def test_missing_fish_never_changes_shell(self):
        with patch.object(bootstrap.os, 'access', return_value=False), \
             patch.object(bootstrap.subprocess, 'run') as run:
            with self.assertRaises(RuntimeError):
                bootstrap.configure_shell_login(self.machine)
            run.assert_not_called()

    def test_declining_fish_login_only_checks_executable(self):
        from types import SimpleNamespace
        account = SimpleNamespace(pw_shell='/bin/bash', pw_name='example')
        with patch.object(bootstrap.os, 'access', return_value=True), \
             patch.object(bootstrap.pwd, 'getpwuid', return_value=account), \
             patch.object(bootstrap.subprocess, 'run') as run, \
             patch('builtins.input', return_value='n'):
            bootstrap.configure_shell_login(self.machine)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][-2:], ['-c', 'exit 0'])

    def test_fish_login_registers_stable_path_and_saves_previous_shell(self):
        from types import SimpleNamespace
        account = SimpleNamespace(pw_shell='/bin/bash', pw_name='example')
        with patch.dict(os.environ, XDG_STATE_HOME=str(self.root / 'state')), \
             patch.object(bootstrap.os, 'access', return_value=True), \
             patch.object(bootstrap.pwd, 'getpwuid', return_value=account), \
             patch.object(bootstrap.shutil, 'which', return_value='/usr/bin/fixture'), \
             patch.object(Path, 'read_text', return_value='/bin/bash\n'), \
             patch.object(bootstrap.subprocess, 'run') as run, \
             patch('builtins.input', return_value=''):
            bootstrap.configure_shell_login(self.machine)
            self.assertEqual(run.call_count, 3)
            self.assertEqual(run.call_args.args[0],
                             ['sudo', 'chsh', '-s', '/home/example/.nix-profile/bin/fish', 'example'])
        self.assertEqual((self.root / 'state/commander-os/previous-shell.txt').read_text(), '/bin/bash\n')


if __name__ == '__main__':
    unittest.main()

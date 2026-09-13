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
             patch('builtins.input', return_value=answer) as prompt:
            self.assertEqual(bootstrap.main(), 0)
            self.assertEqual(config.read_bytes(), original)
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


if __name__ == '__main__':
    unittest.main()

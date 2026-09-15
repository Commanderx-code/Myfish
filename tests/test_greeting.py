import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import bootstrap
import native


class GreetingTests(unittest.TestCase):
    def test_literal_disabled_and_quiet_in_every_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            config = home / '.config'
            target = config / 'commander-os/greeting.txt'
            target.parent.mkdir(parents=True)
            bin_dir = home / 'bin'
            bin_dir.mkdir()
            fastfetch = bin_dir / 'fastfetch'
            fastfetch.write_text('#!/bin/sh\necho FASTFETCH_FIXTURE\n')
            fastfetch.chmod(0o700)
            marker = home / 'unexpected'
            message = f'Welcome, $USER; $(touch {marker}) `echo nope` %s ⚡'
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                       PATH=str(bin_dir) + os.pathsep + os.environ['PATH'], TERM='xterm-256color')
            env.pop('COMMANDER_QUIET', None)
            for shell in ('bash', 'fish', 'zsh'):
                executable = os.environ.get('COMMANDER_TEST_BASH', 'bash') if shell == 'bash' else shell
                flags = ['--noprofile', '--norc'] if shell == 'bash' else ['--no-config'] if shell == 'fish' else ['-f']
                source = ROOT / ('modules/fish/conf.d/90-welcome.fish' if shell == 'fish' else 'modules/shell/common.sh')
                for text, quiet in ((message, False), ('', False), (message, True)):
                    with self.subTest(shell=shell, text=text, quiet=quiet):
                        target.write_text(text + '\n')
                        run_env = dict(env, **({'COMMANDER_QUIET': '1'} if quiet else {}))
                        result = subprocess.run([executable, *flags, '-i', '-c', f'source "{source}"'], env=run_env, text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual('FASTFETCH_FIXTURE' in result.stdout, not quiet)
                        self.assertEqual(message in result.stdout, bool(text) and not quiet)
                        self.assertNotIn('Hello,', result.stdout)
                        self.assertFalse(marker.exists())

    def test_settings_save_and_native_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            machine = json.loads((ROOT / 'machine.example.json').read_text())
            machine.update(homeDirectory=str(home), shell='zsh')
            config = home / 'machine.json'
            config.write_text(json.dumps(machine))
            for option, expected in [(['--greeting', 'Welcome, {user}!'], 'Welcome, {user}!'),
                                     (['--no-greeting'], ''), (['--default-greeting'], 'Hello, {user} ⚡')]:
                with patch.object(sys, 'argv', ['bootstrap', '--init', '--config', str(config), *option]), patch.object(bootstrap.os, 'geteuid', return_value=1000):
                    self.assertEqual(bootstrap.main(), 0)
                saved = json.loads(config.read_text())
                self.assertEqual(saved['greeting'], expected)
                saved['features']['neovim'] = False
                files = native.config_files(saved, home, home / '.config')
                self.assertEqual(files[home / '.config/commander-os/greeting.txt'], expected.replace('{user}', 'example') + '\n')

    def test_rejects_control_characters_and_non_text(self):
        machine = json.loads((ROOT / 'machine.example.json').read_text())
        for value in (False, None, 'hello\nbye', '\x1b[2J'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bootstrap.validate(dict(machine, greeting=value))

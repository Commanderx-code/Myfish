"""Exercise the actual Starship renderer with shell exit/pipeline statuses."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StarshipTests(unittest.TestCase):
    def test_exit_status_is_numeric_and_success_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp)
            for status, pipeline, expected in [
                ('0', '0', ''), ('1', '1', '[exit 1] '),
                ('127', '127', '[exit 127] '), ('126', '126', '[exit 126] '),
                ('130', '130', '[exit 130] '), ('143', '143', '[exit 143] '),
                ('1', '0 0 1', '[exit 1] '), ('0', '1 0', ''),
                ('1', '1 0 1', '[exit 1] '),
            ]:
                with self.subTest(status=status, pipeline=pipeline):
                    result = subprocess.run(['starship', 'module', 'status', '--status', status,
                                             '--pipestatus', pipeline], cwd=tmp, env=env,
                                            check=True, text=True, capture_output=True)
                    plain = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
                    self.assertEqual(plain, expected)
                    self.assertEqual(result.stderr, '')

    def test_fish_passes_real_command_and_pipeline_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp)
            for command, expected in [('true', ''), ('false', '[exit 1] '),
                                       ('true | false', '[exit 1] '), ('false | true', '')]:
                with self.subTest(command=command):
                    script = command + '\nset -l codes $status $pipestatus\nstarship module status --status=$codes[1] --pipestatus="$codes[2..-1]"'
                    result = subprocess.run(['fish', '--no-config', '-c', script], cwd=tmp, env=env,
                                            check=True, text=True, capture_output=True)
                    self.assertEqual(re.sub(r'\x1b\[[0-9;]*m', '', result.stdout), expected)
                    self.assertEqual(result.stderr, '')

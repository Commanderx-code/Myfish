"""Exercise the actual Starship renderer with shell exit/pipeline statuses."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StarshipTests(unittest.TestCase):
    def test_exit_status_labels_stay_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp)
            for status, pipeline, expected in [
                ('0', '0', ''), ('1', '1', ''),
                ('127', '127', ''), ('126', '126', ''),
                ('130', '130', ''), ('143', '143', ''),
                ('1', '0 0 1', ''), ('0', '1 0', ''),
                ('1', '1 0 1', ''),
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
            for command, expected in [('true', ''), ('false', ''),
                                       ('true | false', ''), ('false | true', '')]:
                with self.subTest(command=command):
                    script = command + '\nset -l codes $status $pipestatus\nstarship module status --status=$codes[1] --pipestatus="$codes[2..-1]"'
                    result = subprocess.run(['fish', '--no-config', '-c', script], cwd=tmp, env=env,
                                            check=True, text=True, capture_output=True)
                    self.assertEqual(re.sub(r'\x1b\[[0-9;]*m', '', result.stdout), expected)
                    self.assertEqual(result.stderr, '')

    def test_character_is_red_cross_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp)
            for status, symbol in [('0', 'λ'), ('1', '×'), ('127', '×'), ('130', '×')]:
                with self.subTest(status=status):
                    result = subprocess.run(['starship', 'module', 'character', '--status', status],
                                            cwd=tmp, env=env, check=True, text=True, capture_output=True)
                    self.assertEqual(re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).strip(), symbol)
                    if status != '0':
                        self.assertRegex(result.stdout, r'\x1b\[[0-9;]*31m')

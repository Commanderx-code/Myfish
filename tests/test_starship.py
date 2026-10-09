"""Exercise the actual Starship renderer with shell exit/pipeline statuses."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
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

    def test_every_named_colour_is_in_each_palette(self):
        text = (ROOT / 'modules/starship.toml').read_text()
        config = tomllib.loads(text)
        names = set(re.findall(r'(?:bg|fg):(\w+)', text))
        self.assertIn(config['palette'], config['palettes'])
        # Powerline separators (U+E0B0) join the segments; an editor can silently drop them.
        self.assertEqual(config['format'].count('\ue0b0'), 6)
        for name, palette in config['palettes'].items():
            with self.subTest(palette=name):
                self.assertLessEqual(names, set(palette))
                for value in palette.values():
                    self.assertRegex(value, r'^#[0-9a-f]{6}$')

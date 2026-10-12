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
            for status, symbol in [('0', '╰─ ❯'), ('1', '╰─ ×'), ('127', '╰─ ×'), ('130', '╰─ ×')]:
                with self.subTest(status=status):
                    result = subprocess.run(['starship', 'module', 'character', '--status', status],
                                            cwd=tmp, env=env, check=True, text=True, capture_output=True)
                    self.assertEqual(re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).strip(), symbol)
                    if status != '0':
                        self.assertRegex(result.stdout, r'\x1b\[[0-9;]*31m')
                        # The connector takes the palette's alert colour.
                        self.assertRegex(result.stdout, r'38;2;241;108;117m╰─')

    def test_git_state_names_the_step_of_a_stopped_rebase(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp,
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
            repo = Path(tmp) / 'repo'
            repo.mkdir()

            def git(*args, check=True):
                subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                                *args], cwd=repo, env=env, check=check, capture_output=True)

            def module():
                result = subprocess.run(['starship', 'module', 'git_state'], cwd=repo, env=env,
                                        check=True, text=True, capture_output=True)
                return re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).strip()

            git('init', '--quiet', '--initial-branch=main')
            for branch, text in [(None, 'one'), ('feature', 'two'), ('main', 'three')]:
                if branch:
                    git('switch', '--quiet', *(['--create'] if branch == 'feature' else []), branch)
                (repo / 'file').write_text(text + '\n')
                git('add', 'file')
                git('commit', '--quiet', '--message', text)
            self.assertEqual(module(), '')
            git('switch', '--quiet', 'feature')
            git('rebase', 'main', check=False)
            self.assertEqual(module(), 'REBASING 1/1')

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

    def test_subshell_markers_show_only_inside_a_subshell(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp,
                        SHLVL='1')
            for name in ('IN_NIX_SHELL', 'name', 'NVIM', 'YAZI_LEVEL', 'NNNLVL'):
                base.pop(name, None)
            for extra, expected in [
                ({}, ''),
                ({'IN_NIX_SHELL': 'impure', 'name': 'devshell'}, '\uf313 devshell'),
                ({'NVIM': '/run/user/1000/nvim.1.0'}, 'nvim'),
                ({'YAZI_LEVEL': '1'}, 'yazi'),
                ({'NNNLVL': '1'}, 'nnn'),
                ({'SHLVL': '2'}, '↕2'),
                ({'SHLVL': '3', 'YAZI_LEVEL': '1'}, 'yazi ↕3'),
            ]:
                with self.subTest(extra=extra):
                    result = subprocess.run(['starship', 'prompt'], cwd=tmp, env=dict(base, **extra),
                                            check=True, text=True, capture_output=True)
                    plain = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
                    # The first segment is the username, then any markers.
                    segment = plain.split('╭─', 1)[1].split('\ue0b0', 1)[0]
                    marker = segment.split(' ', 1)[1].strip()
                    self.assertEqual(marker, expected)
                    self.assertEqual(result.stderr, '')

    def test_package_version_stays_off_the_input_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, STARSHIP_CONFIG=str(ROOT / 'modules/starship.toml'), STARSHIP_CACHE=tmp)
            (Path(tmp) / 'package.json').write_text('{"name": "fixture", "version": "1.2.3"}\n')
            result = subprocess.run(['starship', 'prompt'], cwd=tmp, env=env,
                                    check=True, text=True, capture_output=True)
            bar, entry = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', result.stdout).strip().splitlines()
            self.assertIn('1.2.3', bar)
            self.assertEqual(entry.strip(), '╰─ ❯')

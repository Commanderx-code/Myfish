import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FishTests(unittest.TestCase):
    def test_all_fish_files_parse(self):
        for source in (ROOT / 'modules/fish').rglob('*.fish'):
            with self.subTest(source=source.name):
                subprocess.run(['fish', '--no-config', '--no-execute', str(source)], check=True, capture_output=True)

    def test_interactive_startup_and_bindings(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            shutil.copytree(ROOT / 'modules/fish', home / '.config/fish')
            for path in (home / '.config/fish').rglob('*'):
                if path.is_dir():
                    path.chmod(0o700)
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                       XDG_DATA_HOME=str(home / '.local/share'), XDG_CACHE_HOME=str(home / '.cache'),
                       XDG_STATE_HOME=str(home / '.local/state'), COMMANDER_QUIET='1', TERM='xterm-256color')
            result = subprocess.run(['fish', '-i', '-c',
                'fish_user_key_bindings; functions ls; functions ll; bind \\cp; functions __fzf_starstar_tab'],
                env=env, text=True, capture_output=True, check=True)
            self.assertIn('--icons', result.stdout)
            self.assertIn('fzf_open_file', result.stdout)
            self.assertNotIn('Unknown command', result.stderr)
            self.assertNotIn('error:', result.stderr)

    def test_mkcd_handles_spaces(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'a directory'
            result = subprocess.run(['fish', '--no-config', '-c',
                'source $argv[1]; mkcd $argv[2]; pwd',
                str(ROOT / 'modules/fish/functions/mkcd.fish'), str(destination)],
                text=True, capture_output=True, check=True)
            self.assertEqual(result.stdout.strip(), str(destination))

    def test_lazyg_does_not_push_after_failed_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            mock = Path(directory) / 'git'
            mock.write_text('#!/bin/sh\ncase "$1" in commit) exit 7;; push) echo UNEXPECTED_PUSH;; esac\n')
            mock.chmod(0o700)
            env = dict(os.environ, PATH=directory + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['fish', '--no-config', '-c',
                'source $argv[1]; source $argv[2]; lazyg fixture',
                str(ROOT / 'modules/fish/functions/gcom.fish'), str(ROOT / 'modules/fish/functions/lazyg.fish')],
                env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 7)
            self.assertNotIn('UNEXPECTED_PUSH', result.stdout)

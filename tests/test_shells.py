import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShellParityTests(unittest.TestCase):
    def run_shell(self, shell, code, args=(), env=None):
        flags = ['--noprofile', '--norc'] if shell == 'bash' else ['-f']
        executable = os.environ.get('COMMANDER_TEST_BASH', shell) if shell == 'bash' else shell
        return subprocess.run([executable, *flags, '-i', '-c', code, 'test',
                               str(ROOT / 'modules/shell/common.sh'), *map(str, args)],
                              env=dict(os.environ, COMMANDER_QUIET='1', **(env or {})),
                              text=True, capture_output=True)

    def test_bash_and_zsh_navigation_and_aliases(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'with spaces'
                result = self.run_shell(shell, '. "$1"; mkcd "$2" && pwd; alias ll', [target])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(str(target), result.stdout)
                self.assertIn('--icons', result.stdout)

    def test_failed_commit_never_pushes_in_either_shell(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                mock = Path(directory) / 'git'
                mock.write_text('#!/bin/sh\ncase "$1" in commit) exit 7;; push) echo BAD_PUSH;; esac\n')
                mock.chmod(0o700)
                result = self.run_shell(shell, '. "$1"; lazyg fixture',
                                        env={'PATH': directory + os.pathsep + os.environ['PATH']})
                self.assertEqual(result.returncode, 7, result.stderr)
                self.assertNotIn('BAD_PUSH', result.stdout)

    def test_file_picker_preserves_spaces(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                mock = Path(directory)
                for name, text in {
                    'fd': '#!/bin/sh\nprintf "a file.txt\\0"\n',
                    'fzf': '#!/bin/sh\ncat\n',
                    'nvim': '#!/bin/sh\nprintf "picked:%s\\n" "$@"\n',
                }.items():
                    (mock / name).write_text(text)
                    (mock / name).chmod(0o700)
                result = self.run_shell(shell, '. "$1"; fdi',
                                        env={'PATH': directory + os.pathsep + os.environ['PATH']})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('picked:a file.txt', result.stdout)

    def test_binding_adapters_load(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell):
                adapter = ROOT / 'modules/shell' / ('bash.sh' if shell == 'bash' else 'zsh.zsh')
                code = '. "$1"; . "$2"; ' + ('bind -X' if shell == 'bash' else "bindkey '^P'")
                result = self.run_shell(shell, code, [adapter])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('fdi' if shell == 'bash' else 'commander-open', result.stdout)

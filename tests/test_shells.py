import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from shell_support import require_shell

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
                require_shell(self, shell)
                target = Path(directory) / 'with spaces'
                # The listing aliases exist only when eza does, so supply one.
                tools = Path(directory) / 'bin'
                tools.mkdir()
                (tools / 'eza').write_text('#!/bin/sh\n')
                (tools / 'eza').chmod(0o700)
                result = self.run_shell(shell, '. "$1"; mkcd "$2" && pwd; alias ll', [target],
                                        env={'PATH': str(tools) + os.pathsep + os.environ['PATH']})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(str(target), result.stdout)
                self.assertIn('--icons', result.stdout)

    def test_commands_keep_their_meaning_without_the_replacement(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                require_shell(self, shell)
                # A PATH with the shell's own basics but none of eza, bat, rg or fd.
                tools = Path(directory)
                executable = os.environ.get('COMMANDER_TEST_BASH', shell) if shell == 'bash' else shell
                (tools / shell).symlink_to(shutil.which(executable))
                for name in ('uname', 'whoami', 'cat', 'date'):
                    (tools / name).symlink_to(shutil.which(name))
                result = self.run_shell(shell, '. "$1"; alias ls cat grep find; alias ccat cgrep cfind',
                                        env={'PATH': str(tools)})
                for name in ('ls', 'cat', 'grep', 'find'):
                    self.assertNotRegex(result.stdout, rf'(?m)^(alias )?{name}=')
                for name in ('ccat', 'cgrep', 'cfind'):
                    self.assertRegex(result.stdout, rf'(?m)^(alias )?{name}=')

    def test_extract_picks_the_archive_tool(self):
        # Each stand-in tool reports its own name, so the output shows which one ran.
        cases = [('a.rar', ('unrar', '7z'), 'unrar x'), ('a.rar', ('7z',), '7z x'),
                 ('a.rar', ('7zz',), '7zz x'), ('a.7z', ('unrar', '7z'), '7z x')]
        for shell in ['fish', 'bash', 'zsh']:
            for name, available, expected in cases:
                with self.subTest(shell=shell, archive=name, tools=available), \
                        tempfile.TemporaryDirectory() as directory:
                    require_shell(self, shell)
                    tools = Path(directory) / 'bin'
                    tools.mkdir()
                    executable = os.environ.get('COMMANDER_TEST_BASH', shell) if shell == 'bash' else shell
                    (tools / shell).symlink_to(shutil.which(executable))
                    for basic in ('uname', 'whoami', 'realpath'):
                        (tools / basic).symlink_to(shutil.which(basic))
                    for tool in available:
                        (tools / tool).write_text(f'#!/bin/sh\necho "{tool} $1"\n')
                        (tools / tool).chmod(0o700)
                    archive = Path(directory) / name
                    archive.touch()
                    env = dict(os.environ, PATH=str(tools), COMMANDER_QUIET='1')
                    if shell == 'fish':
                        command = [str(tools / shell), '--no-config', '-c', 'source $argv[1]; extract $argv[2]',
                                   str(ROOT / 'modules/fish/functions/extract.fish'), str(archive)]
                    else:
                        flags = ['--noprofile', '--norc'] if shell == 'bash' else ['-f']
                        command = [str(tools / shell), *flags, '-i', '-c', '. "$1"; extract "$2"', 'test',
                                   str(ROOT / 'modules/shell/common.sh'), str(archive)]
                    result = subprocess.run(command, env=env, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(expected, result.stdout)

    def test_extract_reports_a_missing_tool_and_bad_input(self):
        for shell in ['fish', 'bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                require_shell(self, shell)
                tools = Path(directory) / 'bin'
                tools.mkdir()
                executable = os.environ.get('COMMANDER_TEST_BASH', shell) if shell == 'bash' else shell
                (tools / shell).symlink_to(shutil.which(executable))
                for basic in ('uname', 'whoami', 'realpath'):
                    (tools / basic).symlink_to(shutil.which(basic))
                env = dict(os.environ, PATH=str(tools), COMMANDER_QUIET='1')
                for name, message in [('a.7z', 'Install 7-Zip'), ('a.txt', 'Unsupported archive'),
                                      ('missing.zip', 'Usage: extract')]:
                    archive = Path(directory) / name
                    if not name.startswith('missing'):
                        archive.touch()
                    if shell == 'fish':
                        command = [str(tools / shell), '--no-config', '-c', 'source $argv[1]; extract $argv[2]',
                                   str(ROOT / 'modules/fish/functions/extract.fish'), str(archive)]
                    else:
                        flags = ['--noprofile', '--norc'] if shell == 'bash' else ['-f']
                        command = [str(tools / shell), *flags, '-i', '-c', '. "$1"; extract "$2"', 'test',
                                   str(ROOT / 'modules/shell/common.sh'), str(archive)]
                    result = subprocess.run(command, env=env, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn(message, result.stderr)

    def test_failed_commit_never_pushes_in_either_shell(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell), tempfile.TemporaryDirectory() as directory:
                require_shell(self, shell)
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
                require_shell(self, shell)
                mock = Path(directory)
                for name, text in {
                    'fd': '#!/bin/sh\nprintf "%s\\0" "$TEST_PICK"\n',
                    'fzf': '#!/bin/sh\ncat\n',
                    'nvim': '#!/bin/sh\nprintf "picked:%s\\n" "$@"\n',
                }.items():
                    (mock / name).write_text(text)
                    (mock / name).chmod(0o700)
                # The second name must reach the editor after --, not as an option.
                for name in ('a file.txt', '-c:quit'):
                    result = self.run_shell(shell, '. "$1"; fdi',
                                            env={'PATH': directory + os.pathsep + os.environ['PATH'],
                                                 'TEST_PICK': name})
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('picked:--\npicked:' + name, result.stdout)

    def test_binding_adapters_load(self):
        for shell in ['bash', 'zsh']:
            with self.subTest(shell=shell):
                require_shell(self, shell)
                adapter = ROOT / 'modules/shell' / ('bash.sh' if shell == 'bash' else 'zsh.zsh')
                code = '. "$1"; . "$2"; ' + ('bind -X' if shell == 'bash' else "bindkey '^P'")
                result = self.run_shell(shell, code, [adapter])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('fdi' if shell == 'bash' else 'commander-open', result.stdout)

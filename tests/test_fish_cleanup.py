"""Regression checks for shell helpers; all external actions use fixtures."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = ROOT / 'modules/fish/functions'
FISH = shutil.which('fish')


class FishCleanupTests(unittest.TestCase):
    def test_picker_falls_back_to_debian_fdfind(self):
        self.env['PATH'] = str(self.bin)
        target = self.root / 'a directory'
        target.mkdir()
        self.env['TEST_PICK'] = str(target)
        self.mock('fdfind', 'printf "%s\\0" "$TEST_PICK"')
        self.mock('fzf', '/bin/cat')
        result = self.run_fish('cdi; printf "%s" "$PWD"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, str(target))

    def test_picker_reports_missing_finder(self):
        self.env['PATH'] = str(self.bin)
        self.mock('fzf', '/bin/cat')
        result = self.run_fish('cdi')
        self.assertEqual(result.returncode, 127, result.stderr)
        self.assertIn('Install fd', result.stderr)

    def test_file_picker_preserves_newlines_and_escapes_shell_input(self):
        preview = self.root / '.local/bin/fzf-preview'
        preview.parent.mkdir(parents=True)
        preview.write_text('#!/bin/sh\n')
        preview.chmod(0o700)
        target = self.root / 'space and\nnewline; echo unsafe'
        target.touch()
        self.env['TEST_PICK'] = str(target)
        self.mock('fd', 'printf "%s\\0" "$TEST_PICK"')
        self.mock('fzf', '/bin/cat')
        self.mock('nvim', 'printf "%s" "$1"')
        result = self.run_fish('''function commandline
    if test "$argv[1]" = -r
        eval "$argv[3]"
    end
end
fdi
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, str(target))

    def test_environment_preserves_overrides_without_universal_path_writes(self):
        self.env.update(EDITOR='custom-editor', VISUAL='custom-visual', BAT_PAGER='custom-pager')
        local_bin = self.root / '.local/bin'
        local_bin.mkdir(parents=True)
        result = self.run_fish('source "$argv[1]"; source "$argv[1]"; '
                               'printf "%s\\n" "$EDITOR" "$VISUAL" "$BAT_PAGER"; '
                               'contains -- "$HOME/.local/bin" $PATH; or exit 42; '
                               'set -qU fish_user_paths; and exit 43; exit 0',
                               str(ROOT / 'modules/fish/conf.d/05-environment.fish'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['custom-editor', 'custom-visual', 'custom-pager'])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='fish-cleanup-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'calls'
        self.env = dict(os.environ, HOME=str(self.root), XDG_CONFIG_HOME=str(self.root / 'config'), PATH=str(self.bin) + ':' + os.environ['PATH'],
                        TEST_LOG=str(self.log), TMPDIR=str(self.root))


    def mock(self, name, body):
        path = self.bin / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)


    def run_fish(self, code, *args):
        return subprocess.run([FISH, '--no-config', '-c',
                               'set -p fish_function_path $argv[1]; set -e argv[1]; ' + code,
                               str(FUNCTIONS), *args], env=self.env, cwd=self.root,
                              capture_output=True, text=True, timeout=15)


    def test_lazyg_checks_arguments_and_stops_on_git_failures(self):
        self.mock('git', 'printf "%s\\n" "$*" >> "$TEST_LOG"\n'
                  '[ "$1" != "$TEST_FAIL" ] || exit 42')
        result = self.run_fish('lazyg')
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.log.exists())
        for failure, expected in [('add', ['add .']),
                                  ('commit', ['add .', 'commit -m two words']),
                                  ('push', ['add .', 'commit -m two words', 'push']),
                                  ('', ['add .', 'commit -m two words', 'push'])]:
            with self.subTest(failure=failure):
                self.log.unlink(missing_ok=True)
                self.env['TEST_FAIL'] = failure
                result = self.run_fish('lazyg "two words"')
                self.assertEqual(result.returncode, 42 if failure else 0, result.stderr)
                self.assertEqual(self.log.read_text().splitlines(), expected)


    def test_mkcd_stops_when_creation_fails(self):
        self.mock('mkdir', 'exit 42')
        target = self.root / 'already exists'
        target.mkdir()
        result = self.run_fish('mkcd "$argv[1]"; set -l result $status; pwd; exit $result', str(target))
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.root))


    def test_broot_cleans_temp_file_without_trash_and_preserves_failure(self):
        self.mock('broot', 'printf "%s" "$2" > "$TEST_LOG"\n'
                  'printf "false\\n" > "$2"\nexit "${TEST_BROOT_STATUS:-0}"')
        for status, expected in [('0', 1), ('42', 42)]:
            self.env['TEST_BROOT_STATUS'] = status
            result = self.run_fish('function rm; echo TRASH_CALLED; return 99; end; br')
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertNotIn('TRASH_CALLED', result.stdout)
            self.assertFalse(Path(self.log.read_text()).exists())


    def test_tab_calls_widget_as_function_and_preserves_normal_completion(self):
        code = '''function commandline
    if test (count $argv) -eq 1
        printf '%s' "$TEST_TOKEN"
    else
        printf '%s\\n' "$argv" >> "$TEST_LOG"
    end
end
function fzf-file-widget; echo WIDGET; end
__fzf_starstar_tab
'''
        self.env['TEST_TOKEN'] = 'folder with spaces/**'
        result = self.run_fish(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'WIDGET')
        self.assertIn('folder with spaces/', self.log.read_text())
        self.env['TEST_TOKEN'] = 'ordinary'
        self.log.unlink()
        result = self.run_fish(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('WIDGET', result.stdout)
        self.assertIn('complete', self.log.read_text())


    def test_directory_pickers_preserve_unusual_paths_and_cancel(self):
        target = self.root / 'space and\nnewline'
        target.mkdir()
        self.env['TEST_PICK'] = str(target)
        self.mock('fd', 'printf "%s\\n" "$*" >> "$TEST_LOG"\nprintf "%s\\0" "$TEST_PICK"')
        self.mock('fzf', '/bin/cat')
        for function, option in [('fcd', '--max-depth 1'), ('cdi', '--hidden --follow')]:
            result = self.run_fish(function + '; printf "%s" "$PWD"')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, str(target))
            self.assertIn(option, self.log.read_text())
        self.mock('fzf', 'exit 130')
        result = self.run_fish('cdi; pwd')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.root))

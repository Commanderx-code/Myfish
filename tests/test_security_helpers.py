"""Exercise untrusted search/notification data at actual process boundaries."""
import base64
import json
import os
from pathlib import Path
import re
import runpy
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SecurityHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / '.local/bin'
        self.bin.mkdir(parents=True)
        self.log = self.home / 'calls.jsonl'
        self.work = self.home / 'work'
        self.work.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / 'config'),
                        XDG_DATA_HOME=str(self.home / 'data'), XDG_CACHE_HOME=str(self.home / 'cache'),
                        XDG_STATE_HOME=str(self.home / 'state'), COMMANDER_QUIET='1', TERM='xterm-256color',
                        PATH=str(self.bin) + os.pathsep + os.environ['PATH'], TEST_LOG=str(self.log))
        for name in ('KITTY_WINDOW_ID', 'SSH_CLIENT', 'TMUX_PANE', 'SWAYSOCK', 'HYPRLAND_INSTANCE_SIGNATURE'):
            self.env.pop(name, None)
        shutil.copyfile(ROOT / 'modules/fzf-rg', self.bin / 'fzf-rg')
        (self.bin / 'fzf-rg').chmod(0o700)
        for name in ('nvim', 'bat', 'osascript', 'powershell.exe'):
            self.mock(name, "with open(os.environ['TEST_LOG'], 'a') as f: f.write(json.dumps([Path(sys.argv[0]).name, sys.argv[1:]]) + '\\n')")
        self.mock('fzf', """
rows = sys.stdin.buffer.readlines()
if os.environ.get('TEST_CANCEL'): sys.exit(130)
row = rows[0]
preview = sys.argv[sys.argv.index('--preview') + 1]
parts = shlex.split(preview)
parts[-1] = row.split(b'\\t', 1)[0].decode()
subprocess.run(parts, check=True)
sys.stdout.buffer.write(row)
""")

    def mock(self, name, body):
        path = self.bin / name
        path.write_text('#!' + sys.executable + '\nimport os, sys, json, shlex, subprocess\nfrom pathlib import Path\n' + body + '\n')
        path.chmod(0o700)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def search(self, shell):
        if shell == 'fish':
            code = '''set -p fish_function_path $argv[1]
function commandline
    if test "$argv[1]" = -r
        eval "$argv[3]"
    end
end
fzf_rg_search
'''
            command = ['fish', '--no-config', '-c', code, str(ROOT / 'modules/fish/functions')]
        else:
            executable = os.environ.get('COMMANDER_TEST_BASH', shell) if shell == 'bash' else shell
            flags = ['--noprofile', '--norc'] if shell == 'bash' else ['-f']
            command = [executable, *flags, '-i', '-c', '. "$1"; rgi needle', 'test', str(ROOT / 'modules/shell/common.sh')]
        return subprocess.run(command, cwd=self.work, env=self.env, input='needle\n', text=True, capture_output=True, timeout=20)

    def test_search_preserves_paths_and_keeps_payloads_out_of_commands(self):
        names = ['ordinary file.txt', 'note:!touch PWNED:.txt', 'note:1; touch PWNED; #:.txt',
                 '-option:2:name', 'space and\nnewline.txt', 'quote\" \' $() café.txt']
        if sys.platform == 'linux':  # macOS filesystems require valid UTF-8 names.
            names.append('raw-\udcff.txt')
        for shell in ('fish', 'bash', 'zsh'):
            for name in names:
                with self.subTest(shell=shell, name=name):
                    for previous in self.work.iterdir():
                        previous.unlink()
                    path = self.work / name
                    path.write_text('first line\nneedle:!touch PWNED:body\n')
                    self.log.unlink(missing_ok=True)
                    result = self.search(shell)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    calls = self.calls()
                    self.assertEqual([c[0] for c in calls], ['bat', 'nvim'])
                    preview, editor = calls[0][1], calls[1][1]
                    self.assertEqual(preview[preview.index('--highlight-line') + 1], '2')
                    self.assertEqual(editor[:2], ['+2', '--'])
                    for actual in (preview[-1], editor[-1]):
                        self.assertEqual((self.work / actual).resolve(), path.resolve())
                    self.assertFalse((self.work / 'PWNED').exists())
                    path.unlink()

    def test_cancel_and_no_matches_never_launch_editor(self):
        for shell in ('fish', 'bash', 'zsh'):
            for cancel in (False, True):
                with self.subTest(shell=shell, cancel=cancel):
                    if cancel:
                        (self.work / 'match').write_text('needle')
                        self.env['TEST_CANCEL'] = '1'
                    self.log.unlink(missing_ok=True)
                    result = self.search(shell)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(self.calls())
                    (self.work / 'match').unlink(missing_ok=True)
                    self.env.pop('TEST_CANCEL', None)

    def test_invalid_search_metadata_is_rejected(self):
        decode = runpy.run_path(str(ROOT / 'modules/fzf-rg'))['decode']
        for line in ('1; touch PWNED', '!touch PWNED', 0, -1, True, 1.5):
            token = base64.b64encode(json.dumps([base64.b64encode(b'file').decode(), line]).encode())
            with self.subTest(line=line), self.assertRaises(ValueError):
                decode(token)

    def test_partial_search_errors_preserve_readable_matches(self):
        (self.work / 'readable').write_text('needle\n')
        denied = self.work / 'unreadable'
        denied.write_text('needle\n')
        denied.chmod(0)
        try:
            for shell in ('fish', 'bash', 'zsh'):
                with self.subTest(shell=shell):
                    self.log.unlink(missing_ok=True)
                    result = self.search(shell)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('Permission denied', result.stderr)
                    self.assertEqual([c[0] for c in self.calls()], ['bat', 'nvim'])
                    self.assertEqual(Path(self.calls()[-1][1][-1]).name, 'readable')
        finally:
            denied.chmod(0o600)

    def notification(self, backend, title, message, sound):
        self.env.update(TEST_TITLE=title, TEST_MESSAGE=message, TEST_SOUND=str(sound))
        code = '''set -g __done_allow_nongraphical 1
set -g __done_notification_command true
source $argv[1]
set -e __done_notification_command
set -g __done_notify_sound $TEST_SOUND
'''
        if backend == 'powershell':
            code += '__done_windows_notification "$TEST_TITLE" "$TEST_MESSAGE"'
        else:
            code += '''
function type
    test "$argv[2]" = osascript
end
function __done_is_process_window_focused; return 1; end
function pwd; printf '/%s' "$TEST_MESSAGE"; end
set -g cmd_duration 6001
__done_ended 'ordinary command'
'''
        return subprocess.run(['fish', '--no-config', '-i', '-c', code,
                               str(ROOT / 'modules/fish/conf.d/80-done.fish')],
                              cwd=self.work, env=self.env, text=True, capture_output=True, timeout=20)

    def test_applescript_messages_are_separate_arguments(self):
        for sound in (0, 1):
            for message in ('ordinary directory', 'x\\" & (do shell script "touch PWNED") --',
                            '-option\nquotes " café & <>'):
                with self.subTest(sound=sound, message=message):
                    self.log.unlink(missing_ok=True)
                    result = self.notification('apple', 'title', message, sound)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    calls = self.calls()
                    self.assertEqual(len(calls), 1, calls)
                    name, args = calls[0]
                    self.assertEqual(name, 'osascript')
                    self.assertEqual(args[-3], '--')
                    self.assertEqual(args[-2], '/' + message + '/ ordinary command')
                    self.assertNotIn(message, ' '.join(args[:-3]))
                    self.assertIn('item 1 of argv', ' '.join(args[:-3]))
                    self.assertEqual('sound name "Glass"' in ' '.join(args[:-3]), bool(sound))

    def test_powershell_only_embeds_encoded_data_and_uses_xml_text_nodes(self):
        values = ['ordinary text', "$(Start-Process calc.exe) ` \' \" <>& café\n\"@\n"]
        scripts = []
        for sound in (0, 1):
            for value in values:
                with self.subTest(sound=sound, value=value):
                    self.log.unlink(missing_ok=True)
                    result = self.notification('powershell', value, value, sound)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    name, args = self.calls()[-1]
                    self.assertEqual(name, 'powershell.exe')
                    self.assertEqual(args[:3], ['-NoProfile', '-NonInteractive', '-Command'])
                    self.assertEqual(len(args), 4)
                    script = args[3]
                    encoded = re.findall(r"FromBase64String\('([A-Za-z0-9+/=]*)'\)", script)
                    self.assertEqual(len(encoded), 2)
                    self.assertEqual([base64.b64decode(v).decode() for v in encoded], [value, value])
                    self.assertNotIn(value, script)
                    self.assertEqual(script.count('.InnerText ='), 2)
                    scripts.append(re.sub(r"FromBase64String\('[A-Za-z0-9+/=]*'\)", "FromBase64String('DATA')", script))
        self.assertEqual(scripts[0], scripts[1])
        self.assertEqual(scripts[2], scripts[3])

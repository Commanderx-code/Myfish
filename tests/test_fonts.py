import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fonts
import install_state


class FontTests(unittest.TestCase):
    def test_plain_font_does_not_satisfy_nerd_font_requirement(self):
        with patch.object(fonts.shutil, 'which', return_value='/fixture/fc-list'):
            for family, missing in [('JetBrains Mono\n', True), ('Other\nJetBrainsMono Nerd Font Mono,Alias\n', False)]:
                with patch.object(fonts.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, family)):
                    self.assertEqual(fonts.needed(), missing)

    def test_install_is_recorded_and_archive_paths_are_not_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            archive = home / 'fixture.tar.xz'
            with tarfile.open(archive, 'w:xz') as tar:
                for name in [*fonts.FILES, '../unexpected']:
                    content = name.encode()
                    entry = tarfile.TarInfo(name)
                    entry.size = len(content)
                    tar.addfile(entry, io.BytesIO(content))
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            commands = []
            def run(command, **kwargs):
                commands.append(command)
                if command[0] == 'curl':
                    shutil.copyfile(archive, command[-1])
            with patch.dict(os.environ, XDG_DATA_HOME=str(home / 'data'), XDG_STATE_HOME=str(home / 'state')), patch.object(fonts.subprocess, 'run', side_effect=run), patch.object(fonts, 'SHA256', checksum):
                receipt = install_state.load()
                fonts.install(home, receipt)
                installed = home / 'data/fonts/commander-os'
                self.assertEqual({p.name for p in installed.iterdir()}, set(fonts.FILES))
                self.assertFalse((home / 'unexpected').exists())
                self.assertEqual(commands[-1], ['fc-cache', '-f', str(installed)])
                for path, record in install_state.load()['files'].items():
                    self.assertIsNone(record['original'])
                    self.assertEqual(record['installed'], install_state.digest(Path(path)))
                # Corrupt downloads cannot overwrite the installed font files.
                before = (installed / fonts.FILES[0]).read_bytes()
                with patch.object(fonts, 'SHA256', 'incorrect'):
                    with self.assertRaisesRegex(RuntimeError, 'checksum'):
                        fonts.install(home, receipt)
                self.assertEqual((installed / fonts.FILES[0]).read_bytes(), before)

    def test_symlinked_destination_is_refused_before_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / 'real').mkdir()
            (home / 'data').symlink_to(home / 'real', target_is_directory=True)
            with patch.dict(os.environ, XDG_DATA_HOME=str(home / 'data')), patch.object(fonts.subprocess, 'run') as run:
                with self.assertRaisesRegex(RuntimeError, 'symlinked'):
                    fonts.install(home, {'files': {}})
                run.assert_not_called()

import base64
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import lifecycle
import install_state


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.enter(patch.object(Path, 'home', return_value=self.home))
        self.enter(patch.dict(os.environ, HOME=str(self.home), XDG_STATE_HOME=str(self.home / '.state')))
        self.enter(contextlib.redirect_stdout(io.StringIO()))
        self.receipt = {'version': 1, 'backend': 'native', 'files': {}, 'packages': []}

    def enter(self, manager):
        result = manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)
        return result

    def file(self, name='config', contents='installed'):
        path = self.home / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        self.receipt['files'][str(path)] = {'original': None, 'mode': None, 'installed': install_state.digest(path)}
        return path

    def remove(self, apply=True, answers=('REMOVE',), components=None):
        with patch('builtins.input', side_effect=answers), patch.object(lifecycle, 'set_login'), \
             patch.object(lifecycle, 'fallback_shell', return_value='/bin/bash'):
            return lifecycle.remove_native(self.receipt, components or lifecycle.COMPONENTS, apply)

    def test_preview_does_not_write_or_run_commands(self):
        path = self.file()
        with patch.object(lifecycle.subprocess, 'run') as run:
            self.remove(False, ())
            run.assert_not_called()
        self.assertEqual(list(self.home.iterdir()), [path])

    def test_cancel_does_not_write_backups_or_remove(self):
        path = self.file()
        self.remove(answers=('cancel',))
        self.assertEqual(list(self.home.iterdir()), [path])

    def test_removal_backs_up_unchanged_file(self):
        path = self.file()
        self.remove()
        self.assertFalse(path.exists())
        backup = next(install_state.directory().glob('recovery-*/files/config'))
        self.assertEqual(backup.read_text(), 'installed')

    def test_modified_file_survives(self):
        path = self.file()
        path.write_text('user edits')
        self.remove()
        self.assertEqual(path.read_text(), 'user edits')

    def test_original_file_and_mode_restored(self):
        path = self.file()
        self.receipt['files'][str(path)].update(original=base64.b64encode(b'original').decode(), mode=0o600)
        self.remove()
        self.assertEqual(path.read_text(), 'original')
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_new_symlink_survives(self):
        path = self.file()
        path.unlink()
        other = self.home / 'other'
        other.write_text('installed')
        path.symlink_to(other)
        self.remove()
        self.assertTrue(path.is_symlink())
        self.assertEqual(other.read_text(), 'installed')

    def test_outside_home_receipt_rejected(self):
        self.receipt['files']['/etc/profile'] = {'installed': 'x'}
        with self.assertRaises(ValueError):
            self.remove()

    def test_symlinked_parent_rejected_even_inside_home(self):
        (self.home / 'real').mkdir()
        (self.home / 'linked').symlink_to(self.home / 'real')
        with self.assertRaises(ValueError):
            lifecycle.safe_path(self.home / 'linked/profile')

    def test_component_removal_preserves_other_components(self):
        nvim = self.file('.config/nvim/init.lua')
        shell = self.file('.config/fish/config.fish')
        self.remove(components={'neovim'})
        self.assertFalse(nvim.exists())
        self.assertTrue(shell.exists())

    def test_modified_startup_preserves_other_user_lines(self):
        prefix = 'export MY_SETTING=yes\n'
        entry = '\n# Commander-os shell integration\n[ -r "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/init.bash" ] && . "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/init.bash"\n'
        path = self.file('.bashrc', prefix + entry)
        path.write_text(path.read_text() + 'alias custom=true\n')
        self.remove()
        self.assertIn(prefix, path.read_text())
        self.assertIn('alias custom', path.read_text())
        self.assertNotIn('commander-os/init', path.read_text())

    def test_edited_startup_entry_not_deleted(self):
        text = '# Commander-os shell integration\n[ -r "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/init.bash" ] && . "${XDG_CONFIG_HOME:-$HOME/.config}/commander-os/init.bash"; echo custom\n'
        self.assertEqual(lifecycle.strip_startup(text), text)

    def test_cannot_select_unowned_package(self):
        self.file()
        self.receipt.update(packages=['neovim'], manager='apt-get')
        with self.assertRaises(ValueError), patch.object(lifecycle.subprocess, 'run') as run:
            self.remove(answers=('bash',))
            run.assert_not_called()

    def test_failed_package_removal_keeps_config(self):
        path = self.file()
        self.receipt.update(packages=['neovim'], manager='apt-get')
        with patch.object(lifecycle.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['apt-get'])):
            with self.assertRaises(subprocess.CalledProcessError):
                self.remove(answers=('all', 'REMOVE'))
        self.assertTrue(path.exists())

    def test_package_manager_cancel_does_not_forget_ownership(self):
        self.receipt.update(packages=['neovim'], manager='apt-get')
        with patch.object(lifecycle.subprocess, 'run'), patch.object(lifecycle.native, 'package_installed', return_value=True):
            self.remove(answers=('all', 'REMOVE'))
        self.assertEqual(install_state.load()['packages'], ['neovim'])

    def test_record_keeps_first_original_and_private_permissions(self):
        path = self.home / 'file'
        path.write_text('before')
        install_state.capture(self.receipt, path, 'after')
        path.write_text('after')
        install_state.finished(self.receipt, path)
        install_state.capture(self.receipt, path, 'again')
        self.assertEqual(base64.b64decode(self.receipt['files'][str(path)]['original']), b'before')
        self.assertEqual((install_state.directory() / 'installation.json').stat().st_mode & 0o777, 0o600)

    def hm_fixture(self):
        active = self.home / 'generation'
        source = active / 'home-files/.config/fixture'
        source.parent.mkdir(parents=True)
        source.write_text('source /nix/store/pinned-plugin\n')
        source.chmod(0o444)
        target = self.home / '.config/fixture'
        target.parent.mkdir()
        target.symlink_to(source)
        self.enter(patch.object(lifecycle, 'generation', return_value=active))
        self.enter(patch.object(lifecycle, 'fallback_shell', return_value='/bin/bash'))
        self.enter(patch.object(lifecycle, 'nix_tool', side_effect=lambda name: '/tools/' + name))
        self.enter(patch.object(lifecycle, 'modern_profile', return_value=False))
        return active, target

    def test_hm_cancel_never_uninstalls(self):
        active, target = self.hm_fixture()
        with patch.object(lifecycle, 'build_hm', return_value=[Path('/remove')]), \
             patch('builtins.input', return_value='cancel'), patch.object(lifecycle.subprocess, 'run') as run:
            lifecycle.remove_hm({'generation': str(active)}, {}, False, True)
            run.assert_not_called()
        self.assertTrue(target.is_symlink())
        self.assertFalse(install_state.directory().exists())

    def test_hm_build_failure_never_changes_shell(self):
        active, target = self.hm_fixture()
        with patch.object(lifecycle, 'build_hm', side_effect=RuntimeError('failed')), patch.object(lifecycle, 'set_login') as login:
            with self.assertRaises(RuntimeError):
                lifecycle.remove_hm({'generation': str(active)}, {}, True, True)
            login.assert_not_called()
        self.assertTrue(target.is_symlink())

    def test_detach_pins_before_removal_and_copies_editable_files(self):
        active, target = self.hm_fixture()
        events = []
        def run(command, **kwargs):
            events.append(command)
            if command == ['/remove/activate']:
                target.unlink()
        with patch.object(lifecycle, 'build_hm', return_value=[Path('/remove'), Path('/retained')]), \
             patch.object(lifecycle, 'set_login'), patch.object(lifecycle.subprocess, 'run', side_effect=run), \
             patch('builtins.input', return_value='DETACH'):
            lifecycle.remove_hm({'generation': str(active)}, {}, True, True)
        self.assertEqual([event[0] for event in events], ['/tools/nix-store', '/tools/nix-store', '/remove/activate', '/tools/nix-env'])
        self.assertFalse(target.is_symlink())
        self.assertTrue(target.stat().st_mode & 0o200)
        self.assertIn('/nix/store/pinned-plugin', target.read_text())
        self.assertEqual(install_state.load()['backend'], 'detached')

    def test_detach_failure_preserves_recovery_and_safe_shell(self):
        active, target = self.hm_fixture()
        def run(command, **kwargs):
            if command == ['/remove/activate']:
                target.unlink()
            if command[0] == '/tools/nix-env':
                raise RuntimeError('profile failure')
        with patch.object(lifecycle, 'build_hm', return_value=[Path('/remove'), Path('/retained')]), \
             patch.object(lifecycle, 'set_login') as login, patch.object(lifecycle.subprocess, 'run', side_effect=run), \
             patch('builtins.input', return_value='DETACH'), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(RuntimeError):
                lifecycle.remove_hm({'generation': str(active), 'version': 1, 'files': {}, 'packages': []}, {}, True, True)
        login.assert_called_once_with('/bin/bash')
        self.assertTrue(next(install_state.directory().glob('recovery-*/files/.config/fixture')).is_file())
        self.assertEqual(install_state.load()['pending'], 'detach')

    def test_full_reinstall_preserves_disabled_features(self):
        machine = {'shell': 'bash', 'features': {'fish': False, 'neovim': False, 'development': False}}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            lifecycle.reinstall({'backend': 'home-manager'}, machine, self.home / 'machine.json', lifecycle.COMPONENTS, False, False, False)
        self.assertIn('"development": false', output.getvalue())
        self.assertIn('"neovim": false', output.getvalue())

    def test_full_hm_removal_restores_earliest_backup(self):
        active, target = self.hm_fixture()
        target.with_name(target.name + '.commander-os-2').write_text('original')
        target.with_name(target.name + '.commander-os-100').write_text('later')
        def run(command, **kwargs):
            if command == ['/remove/activate']:
                target.unlink()
        with patch.object(lifecycle, 'build_hm', return_value=[Path('/remove')]), \
             patch.object(lifecycle, 'set_login'), patch.object(lifecycle.subprocess, 'run', side_effect=run), \
             patch('builtins.input', return_value='REMOVE'):
            lifecycle.remove_hm({'generation': str(active)}, {}, False, True)
        self.assertEqual(target.read_text(), 'original')

    def test_neovim_removal_allows_reinstall(self):
        path = self.file('.config/nvim/init.lua')
        self.remove(components={'neovim'})
        self.assertFalse(path.parent.exists())
        machine = {'shell': 'keep', 'features': {'fish': False, 'neovim': True, 'development': False}}
        files = lifecycle.native.config_files(machine, self.home, self.home / '.config')
        self.assertIn(path, files)

    def test_native_records_only_previously_absent_packages(self):
        from types import SimpleNamespace
        machine = {'username': 'example', 'homeDirectory': str(self.home), 'system': 'x86_64-linux',
                   'shell': 'keep', 'features': {'fish': False, 'neovim': False, 'development': False}}
        with patch.object(lifecycle.native, 'package_plan', return_value=['eza', 'jq']), \
             patch.object(lifecycle.native, 'package_installed', side_effect=[True, False, True]), \
             patch.object(lifecycle.native.shutil, 'which', return_value='/fixture'), \
             patch.object(lifecycle.native.pwd, 'getpwuid', return_value=SimpleNamespace(pw_name='example')), \
             patch.object(lifecycle.native.subprocess, 'run'), patch('builtins.input', return_value='APPLY'):
            lifecycle.native.install_native(machine, apply=True, install_missing=True, configure_login=lambda *a, **kw: None)
        self.assertEqual(install_state.load()['packages'], ['jq'])

    def test_partially_failed_file_install_is_removable(self):
        path = self.home / 'config'
        install_state.capture(self.receipt, path, 'installed')
        install_state.save(self.receipt)
        path.write_text('installed')  # Simulate a later failure before final receipt update.
        self.receipt = install_state.load()
        self.remove()
        self.assertFalse(path.exists())


    def test_nix_tool_preserves_multicall_name_through_profile_symlinks(self):
        store = self.home / 'store/bin'
        store.mkdir(parents=True)
        (store / 'nix').write_text('fixture')
        for name in ('nix-store', 'nix-env'):
            (store / name).symlink_to('nix')
        profile = self.home / 'profile'
        profile.symlink_to(store.parent)
        for name in ('nix', 'nix-store', 'nix-env'):
            with self.subTest(name=name), patch.object(lifecycle.shutil, 'which', return_value=str(profile / 'bin' / name)):
                self.assertEqual(lifecycle.nix_tool(name), str(store / name))

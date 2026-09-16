import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import editor
import install_state
import native
import lifecycle


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.config = self.home / '.config'
        patcher = patch.dict(os.environ, XDG_STATE_HOME=str(self.home / 'state'))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_migrate_owned_minimal_config_but_preserve_customized_lua(self):
        init = self.config / 'nvim/init.lua'
        receipt = install_state.load()
        native.write_configs({init: 'vim.opt.number = true\n'}, receipt)
        files = editor.config_files(self.config)
        self.assertIn('require("config.lazy")', files[init])
        native.write_configs(files, receipt)
        self.assertIn(init, editor.config_files(self.config))
        options = self.config / 'nvim/lua/config/options.lua'
        options.write_text('-- user customization\n')
        self.assertEqual(editor.config_files(self.config), {})
        self.assertEqual(options.read_text(), '-- user customization\n')

    def test_unowned_and_symlinked_config_is_preserved(self):
        root = self.config / 'nvim'
        root.mkdir(parents=True)
        self.assertEqual(editor.config_files(self.config), {})
        root.rmdir()
        target = self.home / 'personal'
        target.mkdir()
        root.symlink_to(target, target_is_directory=True)
        self.assertEqual(editor.config_files(self.config), {})

    def test_version_gate_rejects_old_or_unrunnable_tools(self):
        for version, expected in [('NVIM v0.9.5\n', False), ('NVIM v0.11.2\n', True), ('NVIM v0.12.0\n', True)]:
            with patch.object(editor, 'executable', return_value='nvim'), patch.object(editor.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, version)):
                self.assertEqual(editor.recent('nvim', (0, 11, 2), self.home), expected)
        with patch.object(editor, 'executable', return_value='nvim'), patch.object(editor.subprocess, 'run', side_effect=OSError('unsupported binary')):
            self.assertFalse(editor.recent('nvim', (0, 11, 2), self.home))

    def test_download_checksum_rejects_corruption(self):
        target = self.home / 'download'
        target.write_bytes(b'bad download')
        with patch.object(editor.subprocess, 'run'), self.assertRaisesRegex(RuntimeError, 'checksum'):
            editor.download('https://example.invalid/archive', '0'*64, target)

    def test_tool_ownership_and_custom_tool_protection(self):
        tool = self.home / '.local/bin/tree-sitter'
        receipt = install_state.load()
        editor.write_tools(self.home, {tool: (b'#!/bin/sh\n', 0o755)}, receipt)
        self.assertEqual(receipt['files'][str(tool)]['installed'], install_state.digest(tool))
        tool.write_bytes(b'custom')
        with self.assertRaisesRegex(RuntimeError, 'custom editor tool'):
            editor.write_tools(self.home, {tool: (b'replacement', 0o755)}, receipt)
        self.assertEqual(tool.read_bytes(), b'custom')

    def test_removal_tracks_editor_tools_and_cleans_empty_starter_directories(self):
        receipt = install_state.load()
        native.write_configs(editor.config_files(self.config), receipt)
        receipt.update(backend='native', manager='apt-get')
        with patch.object(Path, 'home', return_value=self.home), patch('builtins.input', return_value='REMOVE'):
            self.assertEqual(lifecycle.component(self.home / '.local/bin/tree-sitter'), 'neovim')
            self.assertEqual(lifecycle.component(self.home / '.local/share/commander-os/nvim/0.11.6/bin/nvim'), 'neovim')
            lifecycle.remove_native(receipt, {'neovim'}, True)
        self.assertFalse((self.config / 'nvim').exists())
        self.assertIn(self.config / 'nvim/init.lua', editor.config_files(self.config))

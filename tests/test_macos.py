"""Mac installation boundaries, tested without installing packages or changing accounts."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import host
import native
import lifecycle


class MacTests(unittest.TestCase):
    def machine(self, home, shell):
        return dict(username='example', homeDirectory=str(home), system='aarch64-darwin',
                    shell=shell, features=dict(fish=shell == 'fish', neovim=False, development=True))

    def test_architecture_detection(self):
        for os_name, cpu, expected in [('Darwin', 'arm64', 'aarch64-darwin'),
                                       ('Darwin', 'x86_64', 'x86_64-darwin'),
                                       ('Linux', 'aarch64', 'aarch64-linux')]:
            with patch.object(host.platform, 'system', return_value=os_name), patch.object(host.platform, 'machine', return_value=cpu):
                self.assertEqual(host.system(), expected)

    def test_brew_shell_paths_and_fallback(self):
        with patch.object(host, 'is_macos', return_value=True), patch.object(host, 'brew_prefix', return_value=Path('/opt/homebrew')):
            self.assertEqual(host.native_shell_paths('bash'), [Path('/opt/homebrew/bin/bash'), Path('/opt/homebrew/opt/bash/bin/bash')])
            self.assertEqual(host.fallback_shell(), '/bin/zsh')

    def test_packages_include_shell_even_when_system_shell_exists(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(native.shutil, 'which', return_value='/usr/bin/tool'), patch.object(native, 'package_installed', return_value=False):
            self.assertIn('bash', native.package_plan(self.machine(tmp, 'bash'), 'brew'))
            packages = native.package_plan(self.machine(tmp, 'zsh'), 'brew')
            self.assertTrue({'zsh', 'zsh-autosuggestions', 'zsh-syntax-highlighting', 'trash-cli'}.issubset(packages))

    def test_missing_tools_and_existing_formulae(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(native.shutil, 'which', return_value=None), patch.object(native, 'package_installed', return_value=False):
            packages = native.package_plan(self.machine(tmp, 'bash'), 'brew')
            self.assertTrue({'fastfetch', 'starship', 'fd', 'gnu-tar', 'coreutils', 'make', 'sevenzip', 'lazygit'}.issubset(packages))
            self.assertNotIn('fd-find', packages)
            with patch.object(native, 'package_installed', return_value=True):
                self.assertEqual(native.package_plan(self.machine(tmp, 'bash'), 'brew'), [])

    def test_brew_transactions_split_casks_and_never_sudo(self):
        with patch.object(native.subprocess, 'run') as run:
            native.brew_install(['fish', native.MAC_FONT])
            self.assertEqual([c.args[0] for c in run.call_args_list], [
                ['brew', 'install', '--formula', 'fish'], ['brew', 'install', '--cask', native.MAC_FONT]])
            run.reset_mock()
            native.brew_uninstall(['fish', native.MAC_FONT])
            for call in run.call_args_list:
                self.assertEqual(call.args[0][:2], ['brew', 'uninstall'])
                self.assertEqual(call.kwargs['env']['HOMEBREW_NO_AUTOREMOVE'], '1')

    def test_cask_receipt_query(self):
        with patch.object(native.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'font 1.0')) as run:
            self.assertTrue(native.package_installed('brew', native.MAC_FONT))
            self.assertIn('--cask', run.call_args.args[0])

    def test_mac_startup_order_and_preservation(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(host, 'is_macos', return_value=True):
            home = Path(tmp)
            config = home / '.config'
            original = 'export PERSONAL_SETTING=yes\n'
            (home / '.bash_profile').write_text(original)
            files = native.config_files(self.machine(home, 'bash'), home, config)
            init = files[config / 'commander-os/init.bash']
            self.assertLess(init.index('macos.sh'), init.index('ble-start.sh'))
            self.assertLess(init.index('ble-start.sh'), init.index('starship init'))
            profile = files[home / '.bash_profile']
            self.assertTrue(profile.startswith(original))
            self.assertEqual(lifecycle.strip_startup(profile).strip(), original.strip())
            zsh = native.config_files(self.machine(home, 'zsh'), home, config)[config / 'commander-os/init.zsh']
            self.assertIn('fzf --zsh', zsh)
            self.assertLess(zsh.index('zsh.zsh'), zsh.index('zsh-autosuggestions.zsh'))
            fish = native.config_files(self.machine(home, 'fish'), home, config)[config / 'fish/conf.d/commander-os.fish']
            self.assertIn('fzf --fish | source', fish)

    def run_prerequisites(self, code):
        # Deliberately use Apple's stock Bash 3.2 on macOS CI, not Nix Bash.
        return subprocess.run(['/bin/bash', '-eu', '-c', 'source "$1"\n' + code,
                               'test', str(ROOT / 'scripts/prerequisites.sh')], text=True, capture_output=True)

    def test_linux_never_bootstraps_brew(self):
        result = self.run_prerequisites('uname() { echo Linux; }; load_homebrew() { exit 99; }; ensure_homebrew')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_brew_and_empty_prerequisite_array(self):
        result = self.run_prerequisites('''
uname() { echo Darwin; }
brew() { if [[ "$1" == shellenv ]]; then echo 'export HOMEBREW_PREFIX=/opt/homebrew'; fi; }
confirm_install() { exit 99; }
ensure_homebrew
[[ "$HOMEBREW_PREFIX" == /opt/homebrew ]]
ensure_packages python3
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_declining_brew_never_downloads(self):
        result = self.run_prerequisites('''
uname() { echo Darwin; }
load_homebrew() { return 1; }
confirm_install() { return 1; }
curl() { echo UNEXPECTED_DOWNLOAD; exit 99; }
ensure_homebrew
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('UNEXPECTED_DOWNLOAD', result.stdout)

    def test_mac_prerequisites_use_formula_names(self):
        result = self.run_prerequisites('''
uname() { echo Darwin; }
brew() { return 1; }
command() { [[ "$2" == curl ]]; }
install_packages() { printf '%s\\n' "$@"; }
ensure_packages python3 curl xz
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['brew', 'python', 'xz'])

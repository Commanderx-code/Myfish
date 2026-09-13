from pathlib import Path
import subprocess
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'scripts/prerequisites.sh'


class PrerequisiteTests(unittest.TestCase):
    def run_shell(self, body):
        return subprocess.run(['bash', '-eu', '-c', 'source "$1"\n' + body, 'test', str(HELPER)],
                              text=True, capture_output=True)

    def test_existing_tools_skip_installation(self):
        result = self.run_shell('''
command() { return 0; }
install_packages() { echo unexpected; return 99; }
ensure_packages python3 git curl xz
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_apt_package_mapping(self):
        result = self.run_shell('''
command() { [[ "$2" == apt-get || "$2" == git || "$2" == curl ]]; }
install_packages() { printf '%s\\n' "$@"; }
ensure_packages python3 git curl xz
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['apt-get', 'python3', 'xz-utils'])

    def test_arch_package_mapping(self):
        result = self.run_shell('''
command() { [[ "$2" == pacman ]]; }
install_packages() { printf '%s\\n' "$@"; }
ensure_packages python3 git curl xz
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['pacman', 'python', 'git', 'curl', 'xz'])

    def test_decline_never_calls_sudo(self):
        result = self.run_shell('''
command() { return 0; }
confirm_install() { return 1; }
sudo() { echo UNEXPECTED-SUDO; return 99; }
install_packages apt-get python3
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('UNEXPECTED-SUDO', result.stdout)

    def test_failed_refresh_stops_before_install(self):
        result = self.run_shell('''
command() { return 0; }
confirm_install() { return 0; }
sudo() { printf '%s\\n' "$*"; return 8; }
install_packages apt-get python3
''')
        self.assertEqual(result.returncode, 8)
        self.assertIn('apt-get update', result.stdout)
        self.assertNotIn('apt-get install', result.stdout)

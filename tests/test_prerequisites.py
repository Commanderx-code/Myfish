from pathlib import Path
import subprocess
import unittest

HELPER = Path(__file__).resolve().parents[1] / 'scripts/prerequisites.sh'


class PrerequisiteTests(unittest.TestCase):
    def run_shell(self, body):
        return subprocess.run(['bash', '-eu', '-c', 'uname() { echo Linux; }\nsource "$1"\n' + body, 'test', str(HELPER)],
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

    def test_intel_macs_are_refused(self):
        for kernel, cpu, supported in [('Darwin', 'x86_64', False), ('Darwin', 'arm64', True), ('Linux', 'x86_64', True)]:
            with self.subTest(kernel=kernel, cpu=cpu):
                result = subprocess.run(['bash', '-eu', '-c', 'kernel=$2 cpu=$3\n'
                                         'uname() { if [[ "$1" == -m ]]; then echo "$cpu"; else echo "$kernel"; fi; }\n'
                                         'source "$1"\nrequire_supported_mac', 'test', str(HELPER), kernel, cpu],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode == 0, supported, result.stderr)
                self.assertEqual('Intel Macs are not supported' in result.stderr, not supported)

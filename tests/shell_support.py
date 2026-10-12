"""Let the shell parity tests run on a machine without every shell."""
import os
import shutil


def require_shell(test, shell):
    """Skip the current subtest when the shell is missing, except in CI."""
    if not shutil.which(shell) and not os.environ.get('CI'):
        test.skipTest(f'{shell} is not installed')

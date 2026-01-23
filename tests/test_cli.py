import subprocess
import sys

from fastcs_xspress import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "fastcs_xspress", "--version"]
    stdout = subprocess.check_output(cmd).decode().strip()
    assert __version__ in stdout

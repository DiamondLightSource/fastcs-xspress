import subprocess
import sys

from fastcs_xspress import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "fastcs_xspress", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__

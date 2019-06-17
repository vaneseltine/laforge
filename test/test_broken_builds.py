from laforge.command import build
from pathlib import Path
import pytest
import os

BROKEN_HOME = Path(__file__).parent / "broken"


def force_fail():
    raise RuntimeError("Fulfulling xfail but this isn't applicable on this machine.")


@pytest.mark.xfail
def test_broken_unc_path(specific_computers, capfd):
    if os.environ.get("HOMEDRIVE") != "U:":
        force_fail()
    buildpath = BROKEN_HOME / "unc_path.ini"
    build(buildpath)
    captured = capfd.readouterr()
    assert "not supported" not in captured.err

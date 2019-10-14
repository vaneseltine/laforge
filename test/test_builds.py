from pathlib import Path

import pytest

from laforge import build

BUILD = Path("./buildfiles")
DATA = Path("./data")
SMALL = DATA / "small.csv"


class TestBuildFiles:
    def test_csvs(self, make_temp):
        buildfile = make_temp(BUILD / "csvs.py", SMALL)
        build(buildfile)
        assert 0

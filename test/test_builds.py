from pathlib import Path

from laforge import build

TEST_DIR = Path(__file__).parent
BUILD_DIR = TEST_DIR / "buildfiles"
DATA_DIR = TEST_DIR / "data"
SMALL = DATA_DIR / "small.csv"


class TestBuildFiles:
    def test_csvs(self, make_temp, equal_csvs):
        buildfile = make_temp(BUILD_DIR / "csvs.py", SMALL)
        build(buildfile)
        assert equal_csvs(SMALL, buildfile.parent / "small_out.csv")


class TestCommandLine:

    KEYWORDS = BUILD_DIR / "keywords.py"

    def test_keywords_include(self):
        build(buildfile=self.KEYWORDS, include="good")

    def test_keywords_exclude(self):
        build(buildfile=self.KEYWORDS, exclude="bad")

    def test_keywords_avoid_underscored(self):
        build(buildfile=self.KEYWORDS, include="never")

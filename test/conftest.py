import shutil
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).parent
BUILDFILES = TEST_DIR / "buildfiles"


@pytest.fixture
def equal_csvs():
    def equal_checker(path1, path2):
        text1 = Path(path1).read_text()
        text2 = Path(path2).read_text()
        print(text1)
        print(text2)
        return text1 == text2

    return equal_checker


@pytest.fixture
def make_temp(tmp_path):
    """Move the buildfile and other specified files into a temp folder.

    Flattens structure (i.e,. everything is moved to a single folder).

    Returns the location of the buildfile.
    """

    def temp_maker(*files):
        first_file = None
        for original in files:
            temp_version = tmp_path / Path(original).name
            if not first_file:
                first_file = temp_version
            shutil.copy(original, temp_version)
        return first_file

    return temp_maker

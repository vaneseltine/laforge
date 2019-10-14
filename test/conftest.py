import shutil
from pathlib import Path

import pytest

BUILDFILES = Path("./buildfiles")


@pytest.fixture()
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

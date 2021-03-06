import os
import sys
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import dotenv
import pandas as pd
import pytest
from click.testing import CliRunner

from laforge.builder import Verb
from laforge.distros import Distro
from laforge.sql import Channel, Table

# Pull variables, especially LFTEST_*, into os.environ
dotenv.load_dotenv(dotenv.find_dotenv())
DISTROS = set(Distro.known())
TEST_DISTRO = os.environ.get("LFTEST_DISTRO", "sqlite").lower()
SAMPLES = {f.stem: pd.read_csv(f.resolve()) for f in Path(".").glob("**/*.csv")}

# Hooks and skips


def pytest_runtest_teardown(item, nextitem):
    pass


def pytest_runtest_setup(item):
    Channel.known_channels.clear()
    Channel.known_engines.clear()
    string_markers = stringify_markers(item.iter_markers())
    skip_by_markers(string_markers)
    skip_by_sql(item)


def skip_by_sql(item):
    try:
        # TODO -- there is presumably a more appropriate way to gather this
        parameters = set(item.name.lower()[:-1].split("[")[1].split("-"))
    except IndexError:
        return None
    else:
        param_distros = DISTROS.intersection(parameters)
        if not param_distros:
            return None
        if TEST_DISTRO not in param_distros:
            pytest.skip(f"Intended for {'; '.join(param_distros)} not {TEST_DISTRO}")


def stringify_markers(iter_markers):
    markers = set(mark.name for mark in iter_markers)
    if not markers:
        return []
    return markers


def skip_by_markers(markers):
    platform_skip = platform_violates_mark(markers)
    if platform_skip:
        pytest.skip(platform_skip)


def platform_violates_mark(markers):
    platform_whitelist = {"linux", "win32"}.intersection(markers)
    if not platform_whitelist:
        return 0
    current_platform = sys.platform
    if current_platform in platform_whitelist:
        return 0
    return "Not intended for {}.".format(current_platform)


# Session-scope fixtures


@pytest.fixture(scope="session")
def minimal_df():
    return SAMPLES["small"]


@pytest.fixture(scope="session")
def medium_df():
    return SAMPLES["medium"]


@pytest.fixture(scope="session")
def weird_df():
    df = SAMPLES["weird"]
    df["none"] = None
    df["justanint"] = 64
    df["justanint8"] = df["justanint"].astype(pd.Int8Dtype())
    df["justanint16"] = df["justanint"].astype(pd.Int16Dtype())
    df["stardate"] = pd.Timestamp(2233, 3, 22)
    return df


@pytest.fixture(scope="session")
def test_distro():
    return TEST_DISTRO


@pytest.fixture(scope="session")
def barebones_build():
    return """[task1]
    echo: Hello, galaxy!
    """


# Function-scope fixtures


@pytest.fixture(scope="function")
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="function")
def test_channel(test_distro):
    prefix = f"LFTEST_{test_distro}_".upper()
    crop = len(prefix)
    kwargs = {
        k[crop:].lower(): v for k, v in os.environ.items() if k.startswith(prefix)
    }
    return Channel(distro=test_distro, **kwargs)


@pytest.fixture(scope="function")
def arbitrary_table(test_channel):
    return Table(f"X{uuid.uuid1().hex}", channel=test_channel)


@pytest.fixture(scope="function")
def random_filename(suffix):
    suffix = suffix.name or "." + random_path(3)
    if suffix[0] != ".":
        suffix = "." + suffix
    return ("__TEST_" + random_path() + suffix).lower()


def random_path(crop=None):
    return str(uuid.uuid4())[:crop]


@pytest.fixture(scope="function")
def give_me_path(tmpdir, random_filename):
    def _give_me_path(suffix=None):
        if suffix and not suffix.startswith("."):
            suffix = "." + suffix
        return Path(tmpdir, random_filename).with_suffix(suffix)

    return _give_me_path


@pytest.fixture(scope="function")
def better_tmp_path(tmpdir):
    return Path(tmpdir, str(uuid.uuid4())).with_suffix(".rnd")


@pytest.fixture(scope="module")
def task_config():

    with TemporaryDirectory() as temp_build_dir_location:
        temp_build_dir = Path(temp_build_dir_location)
        working_test_config = {
            "build_dir": temp_build_dir,
            "execute_dir": temp_build_dir,
            "read_dir": temp_build_dir / "data/",
            "write_dir": temp_build_dir / "output/",
            "section": "testsection",
            "dir": {
                Verb.EXECUTE: temp_build_dir,
                Verb.READ: temp_build_dir / "data/",
                Verb.WRITE: temp_build_dir / "output/",
            },
        }

        def test_filename_generator(dir, suffix=None):
            return str(
                working_test_config["dir"][dir]
                / random_path()
                / random_filename(suffix)
            )

        working_test_config["test_filename_generator"] = test_filename_generator
        yield working_test_config
    return 0

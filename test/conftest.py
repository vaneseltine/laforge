import os
import sys
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import dotenv
import pandas as pd
import pytest
from laforge.builder import Verb
from laforge.sql import Channel, Table

# Pull variables, especially LFTEST_*, into os.environ
dotenv.load_dotenv(dotenv.find_dotenv())

DISTROS = ["mysql", "mssql", "postgresql", "sqlite"]
SUPPORTED = [d for d in DISTROS if os.environ.get(f"LFTEST_{d.upper()}") == "1"]

SAMPLES = {f.stem: pd.read_csv(f.resolve()) for f in Path(".").glob("**/*.csv")}


@pytest.fixture(scope="session")
def supported_sqls():
    return SUPPORTED or ["sqlite"]


# Hooks and skips


def pytest_runtest_teardown(item, nextitem):
    pass


def pytest_runtest_setup(item):
    Channel.known_channels.clear()
    Channel.known_engines.clear()
    string_markers = stringify_markers(item.iter_markers())
    skip_by_markers(string_markers)


def stringify_markers(iter_markers):
    markers = set(mark.name for mark in iter_markers)
    if not markers:
        return []
    return markers


def skip_by_markers(markers):
    platform_skip = platform_violates_mark(markers)
    if platform_skip:
        pytest.skip(platform_skip)

    sql_skip = sql_availability_violates_mark(markers)
    if sql_skip:
        pytest.skip(sql_skip)

    stata_skip = stata_is_required_but_missing(markers)
    if stata_skip:
        pytest.skip(stata_skip)


def stata_is_required_but_missing(markers):
    if "stata" not in markers:
        return 0
    if os.environ.get("stata_executable"):
        return 0
    return "Path to Stata executable not available."


def platform_violates_mark(markers):
    platform_whitelist = {"linux", "win32"}.intersection(markers)
    if not platform_whitelist:
        return 0
    current_platform = sys.platform
    if current_platform in platform_whitelist:
        return 0
    return "Not intended for {}.".format(current_platform)


def sql_availability_violates_mark(markers):
    sql_whitelist = {"postgresql", "mssql", "mysql", "sql", "sqlite"}.intersection(
        markers
    )
    if not sql_whitelist:
        return 0
    if set(supported_sqls).intersection(markers):
        return 0
    return "Requires specific SQL distribution: {}.".format(";".join(sql_whitelist))


# Session-scope fixtures


@pytest.fixture(scope="session")
def minimal_df():
    return SAMPLES["small"]


@pytest.fixture(scope="session")
def medium_df():
    return SAMPLES["medium"]


@pytest.fixture(scope="session")
def test_distro():
    return os.environ.get("LFTEST_DISTRO", "sqlite")


# Function-scope fixtures


@pytest.fixture(scope="function")
def test_channel():
    """
    e.g.
    LFTEST_MYSQL = 1
    LFTEST_MYSQL_SERVER = localhost
    LFTEST_MYSQL_DATABASE = test_mason
    LFTEST_MYSQL_SCHEMA = test_mason
    LFTEST_MYSQL_USERNAME = test_mason
    LFTEST_MYSQL_PASSWORD = test_mason
    """

    distro = os.environ.get("LFTEST_DISTRO", "sqlite")
    prefix = f"LFTEST_{distro}_".upper()
    crop = len(prefix)
    kwargs = {
        k[crop:].lower(): v for k, v in os.environ.items() if k.startswith(prefix)
    }
    return Channel(distro=distro, **kwargs)


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
            "shell_dir": temp_build_dir,
            "read_dir": temp_build_dir / "data/",
            "write_dir": temp_build_dir / "output/",
            "section": "testsection",
            "dir": {
                Verb.EXECUTE: temp_build_dir,
                Verb.SHELL: temp_build_dir,
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

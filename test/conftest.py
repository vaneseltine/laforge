import sys
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from laforge.builder import Verb
from laforge.sql import Channel, Table

try:
    from test.secret_config import secrets as SECRETS
except (ImportError, ModuleNotFoundError):
    SECRETS = {"sqlite": {"distro": "sqlite", "database": ":memory:"}}
    SECRETS["sql"] = SECRETS["sqlite"]

TEST_DIR = Path(__file__).parent / "test"
TEST_SAMPLES = TEST_DIR / "samples"


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
    if SECRETS.get("stata_executable"):
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
    current_sql_types = set(SECRETS)
    if current_sql_types:
        current_sql_types.add("sql")
    else:
        return "Requires SQL."
    if current_sql_types.intersection(markers):
        return 0
    return "Requires specific SQL distribution: {}.".format(";".join(sql_whitelist))


# fixtures


@pytest.fixture(scope="session")
def secrets():
    yield SECRETS
    return 0


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


@pytest.fixture(scope="session")
def unimportant_df():
    return pd.DataFrame(
        [(2, "o"), (0, "n"), (0, "i"), (8, "!")], columns=["alpha", "beta"]
    )


@pytest.fixture()
def minimal_df():
    return pd.DataFrame([0])


@pytest.fixture(scope="session")
def prior_results(unimportant_df):
    return unimportant_df


@pytest.fixture()
def random_filename(suffix):
    suffix = suffix.name or "." + random_path()[:3]
    if suffix[0] != ".":
        suffix = "." + suffix
    return ("__TEST_" + random_path() + suffix).lower()


def random_path():
    return str(uuid.uuid4())[:13]


@pytest.fixture()
def make_temp_table(request, secrets):
    created_tables = []

    def _make_temp_table(category="sql"):
        if hasattr(category, "name"):
            category = category.name
        skip_by_markers([category])
        c = Channel(**secrets[category])
        t = Table(request.function.__name__, channel=c)
        created_tables.append(t)
        return t

    yield _make_temp_table

    for t in created_tables:
        t.drop(ignore_existence=True)


@pytest.fixture(scope="module")
def make_channel(secrets):
    def _make_channel(category="sql"):
        if hasattr(category, "name"):
            category = category.name
        skip_by_markers([category])
        return Channel(**secrets[category])

    return _make_channel


@pytest.fixture()
def temp_config():
    with TemporaryDirectory() as temp_build_dir:
        cfg = {"build_dir": Path(temp_build_dir)}
        cfg.update(SECRETS)
        yield cfg


@pytest.fixture()
def give_me_path(tmpdir, random_filename):
    def _give_me_path(suffix=None):
        if suffix and not suffix.startswith("."):
            suffix = "." + suffix
        return Path(tmpdir, random_filename).with_suffix(suffix)

    return _give_me_path

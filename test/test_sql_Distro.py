import pandas as pd
import pytest
import sqlalchemy as sa

from laforge.distros import Distro, SQLDistroNotFound


def test_get_exactly_one_distro_canonically(test_distro):
    try:
        result = Distro.get(test_distro)
        assert test_distro.lower() == result.name.lower()
    except ModuleNotFoundError:
        pytest.skip(f"Missing {test_distro} module.")


@pytest.mark.parametrize(
    "canonical, incoming",
    [
        ("mssql", "microsoft sql server 15.0"),
        ("mssql", "microsoft sql server"),
        ("mssql", "microsoft sql"),
        ("mssql", "ms sql"),
        ("mssql", "mssql"),
        ("mssql", "sql server 14.0"),
        ("mssql", "sql server"),
        ("mysql", "maria"),
        ("mysql", "mariadb"),
        ("mysql", "mysql"),
        ("postgresql", "post gre"),
        ("postgresql", "postgre"),
        ("sqlite", "sqlite3"),
    ],
)
def test_get_exactly_one_distro_variants(canonical, incoming):
    try:
        assert Distro.get(incoming).name == canonical
        assert Distro.get(incoming.upper()).name == canonical
    except ModuleNotFoundError:
        pytest.skip(f"Missing {canonical} module.")


@pytest.mark.parametrize("badname", ["", 293, "asdf"])
def test_fail_bad_distros(badname):
    with pytest.raises(SQLDistroNotFound):
        Distro.get(badname)


@pytest.mark.parametrize(
    "vaguename", ["sql", "m sql", "MSQL", "MYSQL SERVER", "SQLITE SERVER"]
)
def test_fail_vague_distros(vaguename):
    with pytest.raises(SQLDistroNotFound):
        Distro.get(vaguename)


class FakeKwargs:
    @staticmethod
    def pop(key):
        return str(key)


@pytest.mark.parametrize("db", ["", ":memory:", "sqlite.db"])
def test_prepare_for_sqlite_engine(db, tmp_path):
    result = Distro.get("sqlite")
    if db == "sqlite.db":
        db = tmp_path / "sqlite.db"
    url, _ = result.create_spec(server="srvr", database=db, engine_kwargs={})
    assert str(db or ":memory:") in url


def test_prepare_for_other_engines(test_distro):
    if test_distro == "sqlite":
        pytest.skip("sqlite handled elsewhere")
    try:
        result = Distro.get(test_distro)
    except ModuleNotFoundError:
        pytest.skip(f"Missing {test_distro} module.")
    url, _ = result.create_spec(server="srvr", database="db", engine_kwargs=FakeKwargs)
    assert test_distro in url


@pytest.mark.parametrize("dtype", [int, pd.np.int64, pd.np.float64])
@pytest.mark.parametrize("factor", [1, 10, 100])
@pytest.mark.parametrize("i", [2 ** 31 - 1, 2 ** 31, 2 ** 63 - 1, 2 ** 63, 2 ** 64])
def test_no_integer_overflow_from_numpy(dtype, factor, i):
    """
    numpy int64 can't handle overflow (but does issue warning)
    """
    with pytest.warns(None) as record:
        Distro.NUMERIC_PADDING_FACTOR = factor
        try:
            sequence = [dtype(i)] * 2
        except OverflowError:
            return None
        Distro._well_within_range(sequence, sa.types.INT)
    assert len(record) == 0

import pandas as pd
import pytest
import sqlalchemy as sa

from laforge.distros import Distro, SQLDistroNotFound

CANONICAL_NAMES = ["mssql", "mysql", "postgresql", "sqlite"]


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_get_exactly_one_distro_canonically(name):
    try:
        result = Distro.get(name)
        assert name.lower() == result.name.lower()
    except ModuleNotFoundError:
        pytest.skip(f"Missing {name} module.")


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


@pytest.mark.parametrize("name", ["mssql", "mysql", "postgresql"])
def test_prepare_for_other_engines(name):
    try:
        result = Distro.get(name)
    except ModuleNotFoundError:
        pytest.skip(f"Missing {name} module.")
    url, _ = result.create_spec(server="srvr", database="db", engine_kwargs=FakeKwargs)
    assert name in url


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_dunder_hash(name):
    try:
        d = Distro.get(name)
        assert isinstance(hash(d), int)
    except ModuleNotFoundError:
        pytest.skip(f"Missing {name} module.")


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_dunder_str(name):
    try:
        d = Distro.get(name)
        assert isinstance(str(d), str)
    except ModuleNotFoundError:
        pytest.skip(f"Missing {name} module.")


@pytest.mark.parametrize("name", CANONICAL_NAMES)
def test_dunder_repr(name):
    try:
        d = Distro.get(name)
        assert isinstance(repr(d), str)
        assert " object at 0x" not in repr(d)
    except ModuleNotFoundError:
        pytest.skip(f"Missing {name} module.")


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


@pytest.mark.parametrize("distro", ["mysql", "postgresql"])
@pytest.mark.parametrize(
    "n, expectation",
    [
        (2 ** 4, "SMALLINT"),
        (2 ** 12, "SMALLINT"),
        (2 ** 16, "INT"),
        (2 ** 24, "INT"),
        (2 ** 48, "BIGINT"),
        (2 ** 64, "DOUBLE"),
    ],
)
def test_numeric_data_types_myorpost(n, expectation, distro, make_temp_table):

    Distro.NUMERIC_PADDING_FACTOR = 1
    distrocol = {"postgresql": "data_type", "mysql": "COLUMN_TYPE"}[distro]
    t = make_temp_table(distro)
    t.write(pd.DataFrame([n], columns=["mrcolumnface"]))
    for c in t.columns:
        assert str(c.type).startswith(expectation)
    t.drop()


@pytest.mark.mysql
@pytest.mark.parametrize(
    "n, expectation",
    [
        (2, sa.types.VARCHAR(length=50)),
        (49, sa.types.VARCHAR(length=50)),
        (50, sa.types.VARCHAR(length=50)),
        (51, sa.types.VARCHAR(length=100)),
        (99, sa.types.VARCHAR(length=100)),
        (100, sa.types.VARCHAR(length=100)),
        (101, sa.types.VARCHAR(length=150)),
        (2 ** 15, sa.types.VARCHAR(length=32800)),
        (2 ** 16 - 150, sa.types.VARCHAR(length=65400)),
        # (2 ** 16 - 100, sa.types.LONGTEXT),
        # (2 ** 16 - 50, sa.types.LONGTEXT),
        # (2 ** 16, sa.types.LONGTEXT),
    ],
)
def test_varchar_border_with_picky_sql_alchemy_types(n, expectation, make_temp_table):
    t = make_temp_table("mysql")
    df = pd.DataFrame(["x" * n], columns=["mscolumnface"])
    t.write(df)
    for c in t.columns:
        assert str(c.type) == str(expectation)
    # assert t.columns[0].type.lower() == expectation
    t.drop()

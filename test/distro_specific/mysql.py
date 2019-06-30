import pytest
from laforge.sql import Channel, Table, Script, execute
from laforge.distros import Distro


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
def test_numeric_data_types_myorpost(n, expectation, distro, arbitrary_table):
    Distro.NUMERIC_PADDING_FACTOR = 1
    distrocol = {"postgresql": "data_type", "mysql": "COLUMN_TYPE"}[distro]
    t = arbitrary_table
    t.write(pd.DataFrame([n], columns=["mrcolumnface"]))
    for c in t.columns:
        assert str(c.type).startswith(expectation)
    t.drop()

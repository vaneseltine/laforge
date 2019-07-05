import pytest

# from laforge.sql import Table, Script, execute
from laforge.distros import Distro
import sqlalchemy as sa
import pandas as pd


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
def test_varchar_border_with_picky_sql_alchemy_types(n, expectation, arbitrary_table):
    df = pd.DataFrame(["x" * n], columns=["mscolumnface"])
    arbitrary_table.write(df)
    for c in arbitrary_table.metal.columns:
        assert str(c.type) == str(expectation)
    # assert arbitrary_table.columns[0].type.lower() == expectation
    arbitrary_table.drop()


@pytest.mark.parametrize(
    "n, expectation",
    [
        (2 ** 4, "SMALLINT"),
        (2 ** 12, "SMALLINT"),
        (2 ** 16, "INT"),
        (2 ** 24, "INT"),
        (2 ** 48, "BIGINT"),
        # (2 ** 64 - 100, "DOUBLE"),
    ],
)
def test_numeric_data_types_myorpost(n, expectation, arbitrary_table):
    Distro.NUMERIC_PADDING_FACTOR = 1
    t = arbitrary_table
    t.write(pd.DataFrame([n], columns=["mrcolumnface"]))
    for c in t.metal.columns:
        assert str(c.type).startswith(expectation)
    t.drop()

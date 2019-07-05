import pytest
from laforge.sql import Script, execute
from laforge.distros import Distro
import pandas as pd


def test_script_or_execute_to_df(test_channel):
    stmt = "select * from pg_class where oid >= 13015;"
    scripted_r = Script(stmt).read()
    executed_r = execute(stmt, fetch="df")
    assert scripted_r.equals(executed_r)

    scripted_t = list(Script(stmt).read().itertuples(name=None, index=False))
    executed_t = list(tuple(x) for x in execute(stmt, fetch="tuples"))
    assert scripted_t == executed_t


@pytest.mark.parametrize(
    "n, expectation",
    [(2 ** 4, "SMALLINT"), (2 ** 12, "SMALLINT"), (2 ** 16, "INT"), (2 ** 24, "INT")],
)
def test_numeric_data_types_myorpost(n, expectation, arbitrary_table):
    Distro.NUMERIC_PADDING_FACTOR = 1
    t = arbitrary_table
    t.write(pd.DataFrame([n], columns=["mrcolumnface"]))
    for c in t.metal.columns:
        print(c.type)
        print(expectation)
        assert str(c.type).startswith(expectation)

    t.drop()

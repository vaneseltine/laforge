import pytest
from laforge.sql import Channel, Table, Script, execute
from laforge.distros import Distro

STATEMENTS = {
    "mssql": "select top 10 name, schema_id, type_desc from sys.tables;",
    "postgresql": "select * from pg_class where oid >= 13015;",
}


def test_script_or_execute_to_df(secrets):
    c = Channel(**secrets["sql"])
    stmt = STATEMENTS.get(c.distro.name)
    if not stmt:
        pytest.skip()
    scripted_r = Script(stmt).read()
    executed_r = execute(stmt, fetch="df")
    assert scripted_r.equals(executed_r)

    scripted_t = list(Script(stmt).read().itertuples(name=None, index=False))
    executed_t = list(tuple(x) for x in execute(stmt, fetch="tuples"))
    assert scripted_t == executed_t


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

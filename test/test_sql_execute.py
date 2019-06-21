import pytest
from laforge.sql import Channel, Table, Script, execute
from laforge.distros import Distro


@pytest.mark.mssql
def test_do_not_add_foolish_semicolon(make_channel):
    c = make_channel("mssql")
    Script(
        """
    SELECT 1 FROM SYS.TABLES;
    GO
    SELECT 1 FROM SYS.TABLES
    GO""",
        channel=c,
    ).execute()


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

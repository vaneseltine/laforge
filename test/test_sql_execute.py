import pytest
from laforge.sql import Channel, Table, Script, execute
from test.secret_config import secrets


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
    "mssql": [
        "select top 10 name, schema_id, type_desc from sys.tables;",
        "select * from sys.tables;",
    ],
    "postgresql": ["select * from pg_class where oid >= 13015;"],
}


@pytest.mark.parametrize("stmt", STATEMENTS[secrets["sql"]["distro"]])
def test_script_or_execute_to_df(secrets, stmt):
    # Uses implicit channel
    Channel(**secrets["sql"])
    scripted = Script(stmt).read()
    executed = execute(stmt, fetch="df")
    assert scripted.equals(executed)


@pytest.mark.parametrize("stmt", STATEMENTS[secrets["sql"]["distro"]])
def test_script_or_execute_to_simplified_tuples(secrets, stmt):
    # Uses implicit channel
    Channel(**secrets["sql"])
    scripted = list(Script(stmt).read().itertuples(name=None, index=False))
    executed = list(tuple(x) for x in execute(stmt, fetch="tuples"))
    assert scripted == executed

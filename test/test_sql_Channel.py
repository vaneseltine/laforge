import pytest


from laforge.sql import Channel, Table, Script, SQLChannelNotFound, execute


@pytest.mark.sqlite
def test_hail_mary_execute(tmpdir):
    with pytest.raises(SQLChannelNotFound):
        _ = Channel.grab()
    c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
    _ = Channel.grab()
    c2 = Channel(distro="sqlite", database=tmpdir / "c2.db")
    with pytest.raises(SQLChannelNotFound):
        _ = Channel.grab()


@pytest.mark.sqlite
def test_grab_channel(tmpdir):
    with pytest.raises(SQLChannelNotFound):
        _ = execute("select 1 from sqlite_master;", fetch="tuples")
    c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
    _ = execute("select 1 from sqlite_master;", fetch="tuples")
    c2 = Channel(distro="sqlite", database=tmpdir / "c2.db")
    with pytest.raises(SQLChannelNotFound):
        _ = execute("select 1 from sqlite_master;", fetch="tuples")


@pytest.mark.parametrize("fetch", ["df", "tuples", False])
def test_bad_statements(make_channel, fetch):
    c = make_channel("sqlite")
    with pytest.raises(Exception):
        c.execute_statement("select aoweifjwo from wagurgugbbb;", fetch=fetch)


def test_create_objects_via_channel(secrets):
    c = Channel(**secrets["sql"])
    s = Script("select * from spam;", channel=c)
    t = Table("spam", channel=c)
    assert s.channel == c
    assert t.channel == c


@pytest.mark.mssql
def test_initialize_mssql_channel(secrets):
    c = Channel(**secrets["mssql"])
    # assert bool(channel.execute("select 1 from information_schema.tables;").fetchall())
    assert (
        not Script("select 1 from information_schema.tables;", channel=c)
        .to_table()
        .empty
    )


@pytest.mark.mssql
def test_mssql_finder_finds_created_tables(secrets, unimportant_df):
    c = Channel(**secrets["mssql"])
    schema = secrets["mssql"]["schema"]
    t = Table("laforge_test_tester", schema=schema, channel=c)
    t.drop(ignore_existence=True)
    t.write(unimportant_df)
    assert t.exists()
    assert c.find("laforge_test_tester")
    assert c.find("laforge_%_tester")
    assert c.find("laforge_test_tester", schema_pattern=schema[:-2] + "%")
    assert c.find("laforge_test_tester", schema_pattern=schema)
    t.drop()


@pytest.mark.mssql
def test_mssql_finder_does_not_find_dropped_tables(secrets, unimportant_df):
    c = Channel(**secrets["mssql"])
    schema = secrets["mssql"]["schema"]
    t = Table("laforge_test_tester", schema=schema, channel=c)
    t.write(unimportant_df)
    assert t.exists()
    t.drop()
    assert not t.exists()
    assert not c.find("laforge_test_tester")
    assert not c.find("laforge_%_tester")
    assert not c.find("laforge_test_tester", schema_pattern=schema[:-2] + "%")
    assert not c.find("laforge_test_tester", schema_pattern=schema)


@pytest.mark.mysql
def test_initialize_mysql_channel(secrets):
    c = Channel(**secrets["mysql"])
    assert (
        not Script("select 1 from information_schema.tables;", channel=c)
        .to_table()
        .empty
    )


@pytest.mark.mysql
def test_mysql_finder_finds(secrets, unimportant_df):
    c = Channel(**secrets["mysql"])
    t = Table("laforge_test_tester", channel=c)
    t.drop(ignore_existence=True)
    assert not t.exists()
    assert not c.find("laforge_test_tester")
    t.write(unimportant_df)
    assert t.exists()
    assert c.find("laforge_%")
    assert c.find("laforge_test_tester")


@pytest.mark.mysql
def test_mysql_finder_can_drop_and_confirm(secrets, unimportant_df):
    c = Channel(**secrets["mysql"])
    t = Table("laforge_test_tester", channel=c)
    t.write(unimportant_df)
    assert c.find("laforge_test_tester")
    t.drop()
    assert not c.find("laforge_test_tester")
    assert not t.exists()


@pytest.mark.postgresql
def test_initialize_postgresql_channel(secrets):
    c = Channel(**secrets["postgresql"])
    assert (
        not Script("select 1 from information_schema.tables;", channel=c)
        .to_table()
        .empty
    )


@pytest.mark.postgresql
def test_postgresql_finder_finds(secrets, unimportant_df):
    c = Channel(**secrets["postgresql"])
    t = Table("laforge_test_tester", channel=c)
    t.write(unimportant_df)
    assert c.find("laforge_test_tester")
    t.drop()
    assert not c.find("laforge_test_tester")
    assert not t.exists()


@pytest.mark.postgresql
def test_postgresql_finder_can_drop_and_confirm(secrets, unimportant_df):
    c = Channel(**secrets["postgresql"])
    t = Table("laforge_test_tester", channel=c)
    t.write(unimportant_df)
    assert c.find("laforge_test_tester")
    t.drop()
    assert not c.find("laforge_test_tester")
    assert not t.exists()


def test_initialize_sqlite_channel_memory():
    c = Channel(distro="sqlite", database=":memory:")
    try:
        c.execute_statement("drop table laforge_finder_test;")
    except:
        pass
    c.execute_statement("create table laforge_finder_test (test_int INTEGER);")
    c.execute_statement("insert into laforge_finder_test values (1);")
    c.execute_statement("drop table laforge_finder_test;")


@pytest.mark.parametrize("db", [":memory:", "__test_laforge.db"])
def test_initialize_sqlite_channel_file(tmpdir, db):
    if db != ":memory:":
        db = tmpdir / db
    c = Channel(distro="sqlite", database=db)
    try:
        c.execute_statement("drop table laforge_finder_test;")
    except:
        pass
    c.execute_statement("create table laforge_finder_test (test_int INTEGER);")
    c.execute_statement("insert into laforge_finder_test values (1);")
    c.execute_statement("drop table laforge_finder_test;")


def test_sqlite_finder_finds(secrets, unimportant_df):
    c = Channel(**secrets["sqlite"])
    t = Table("laforge_test_tester", channel=c)
    t.write(unimportant_df)
    assert c.find("laforge_test_tester")
    t.drop()
    assert not c.find("laforge_test_tester")
    assert not t.exists()


def test_sqlite_finder_can_drop_and_confirm(secrets, unimportant_df):
    c = Channel(**secrets["sqlite"])
    t = Table("laforge_test_tester", channel=c)
    t.write(unimportant_df)
    assert c.find("laforge_test_tester")
    t.drop()
    assert not c.find("laforge_test_tester")
    assert not t.exists()

import pytest
from laforge.sql import Channel, Script, SQLChannelNotFound, Table, execute


def test_blind_execute_fails(tmpdir):
    with pytest.raises(SQLChannelNotFound):
        _ = Channel.grab()


def test_blind_execute_with_one_channel(tmpdir):
    c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
    assert Channel.grab() == c1


def test_blind_execute(tmpdir):
    c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
    print(hash(c1))
    c2 = Channel(distro="sqlite", database=tmpdir / "c2.db")
    print(hash(c2))
    c3 = Channel(distro="sqlite", database=tmpdir / "c3.db")
    print(hash(c3))
    assert c1 != c2
    assert c1 != c3
    assert c2 != c3
    assert Channel.grab() == c3


@pytest.mark.parametrize("fetch", ["df", "tuples", False])
def test_bad_statements(test_channel, fetch):
    with pytest.raises(Exception):
        test_channel.execute_statement(
            "select aoweifjwo from wagurgugbbb;", fetch=fetch
        )


def test_create_objects_via_shared_channel(test_channel):
    s = Script("select * from spam;", channel=test_channel)
    t = Table("spam", channel=test_channel)
    assert s.channel == test_channel
    assert t.channel == test_channel


def test_finder_finds_created_tables(test_channel, medium_df):
    c = test_channel
    t = Table("laforge_test_tester", channel=test_channel)
    schema = test_channel.schema
    t.drop(ignore_existence=True)
    t.write(medium_df)
    assert t.exists()
    assert c.find("laforge_test_tester")
    assert c.find("laforge_%_tester")
    if schema:
        assert c.find("laforge_test_tester", schema_pattern=schema[:-2] + "%")
        assert c.find("laforge_test_tester", schema_pattern=schema)
    t.drop()


def test_finder_does_not_find_dropped_tables(test_channel, medium_df):
    c = test_channel
    t = Table("laforge_test_tester", channel=test_channel)
    schema = test_channel.schema
    t.write(medium_df)
    assert t.exists()
    t.drop()
    assert not t.exists()
    assert not c.find("laforge_test_tester")
    assert not c.find("laforge_%_tester")
    if schema:
        assert not c.find("laforge_test_tester", schema_pattern=schema[:-2] + "%")
        assert not c.find("laforge_test_tester", schema_pattern=schema)

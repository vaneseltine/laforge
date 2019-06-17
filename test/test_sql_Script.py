#!/usr/bin/env python3
"""
unit tests

see: py.test --fixtures
"""

import re

import pytest

from laforge.sql import Script, Channel, Identifier


@pytest.mark.parametrize(
    "semi",
    [
        ";",
        ";;",
        ";;;",
        "; ",
        " ;",
        " ; ",
        ";; ",
        " ;;",
        " ;; ",
        " ; ; ",
        "; ; ",
        " ; ;",
    ],
)
@pytest.mark.parametrize("gogo", ["", " ", " go", "go ", " go "])
def test_strip_semis(semi, gogo):
    s = "select 1 from sys.tables" + semi + gogo
    assert Script._normalize_batch_end(s) == "select 1 from sys.tables;"


@pytest.mark.parametrize(
    "s", ["select 1 from sys.i_love_lego", "select 1 from sys.i_love_lego;"]
)
def test_do_not_get_too_angry_at_go(s):
    assert "go" in Script._normalize_batch_end(s)


def test_real_query_with_bad_columns(secrets, caplog):
    stmt = {
        "mssql": "select top 5 1 from information_schema.tables;",
        "postgresql": "select 1, 2 from information_schema.tables limit 5;",
        "mysql": "select 1, 2 from information_schema.tables limit 5;",
        "sqlite": "select 1, 2 from sqlite_master;",
    }[secrets["sql"]["distro"]]

    df = Script(stmt, channel=Channel(**secrets["sql"])).to_table()
    # Builtin SQL drivers return bad column names (blank or '?column?')
    assert "WARNING" in caplog.text
    assert len(df.columns) > 0
    # and there should be no bad columns in the final set
    assert not set(Identifier.BLACKLIST).intersection(df.columns)
    # FYI, this is exactly what this should look like for mssql/postgresql
    # result = list(tuple(x) for x in df.to_records())
    # assert result == [(0, 1, 2), (1, 1, 2), (2, 1, 2), (3, 1, 2), (4, 1, 2)]


def cleanup_whitespace(result):
    return [collapse_whitespace_TEST(q) for q in result]


def collapse_whitespace_TEST(s):
    result = s
    result = re.sub(r"[\n\s ]+", " ", result)
    result = result.strip()
    result = re.sub(" +;", ";", result)
    return result


def test_q_parsing(secrets):
    q = Script("select * from hi.there;", channel=Channel(**secrets["sql"]))
    assert q.parsed == ["select * from hi.there;"]


@pytest.mark.parametrize(
    "inputs, cleaned_expected",
    [
        (
            """eggs spam
    go
    sausage""",
            ["eggs spam;", "sausage;"],
        ),
        (
            """eggs spam;
    go
    sausage""",
            ["eggs spam;", "sausage;"],
        ),
        (
            """eggs spam
         ham
    go;;
    sausage""",
            ["eggs spam ham;", "sausage;"],
        ),
    ],
)
def test_query_parsing_go(inputs, cleaned_expected, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert cleanup_whitespace(s.parsed) == cleaned_expected


@pytest.mark.parametrize(
    "inputs, cleaned_expected",
    [
        ("eggs", ["eggs;"]),
        ("eggs spam go sausage", ["eggs spam go sausage;"]),
        ("eggs spam go; sausage", ["eggs spam go; sausage;"]),
        ("eggs spam ; go sausage", ["eggs spam; go sausage;"]),
        ("eggs spam ;go; sausage", ["eggs spam;go; sausage;"]),
        (
            "eggs spam ; wait a minute go; sausage",
            ["eggs spam; wait a minute go; sausage;"],
        ),
        ("eggs spam --go; sausage", ["eggs spam;"]),
        (
            """eggs spam
    --go
    sausage""",
            ["eggs spam sausage;"],
        ),
    ],
)
def test_query_parsing_ignoring_comments(inputs, cleaned_expected, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert cleanup_whitespace(s.parsed) == cleaned_expected


@pytest.mark.parametrize(
    "inputs, outputs",
    [
        ("spam; --regular ham", ["spam;"]),
        ("spam;--regular ham", ["spam;"]),
        ("spam; ---regular ham", ["spam;"]),
        ("spam;  --regular ham", ["spam;"]),
        ("spam --regular ham;", ["spam;"]),
        ("spam--regular ham;", ["spam;"]),
        ("spam ---regular ham;", ["spam;"]),
        ("spam  --regular ham;", ["spam;"]),
        ("--regular ham", []),
        ("---regular ham", []),
        ("spam; --regular ham", ["spam;"]),
        ("    spam; --regular ham", ["spam;"]),
    ],
)
def test_comments_proper_double_dash(inputs, outputs, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert s.parsed == outputs


@pytest.mark.parametrize(
    "inputs, outputs",
    [
        ("spam and eggs - eggs", ["spam and eggs - eggs;"]),
        ("spam and eggs - - sausage", ["spam and eggs - - sausage;"]),
    ],
)
def test_parsing_ignore_non_double_dash(inputs, outputs, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert s.parsed == outputs


@pytest.mark.parametrize(
    "inputs, outputs",
    [
        ("spam/*eggs*/ham", "spamham;"),
        ("spam\n/*eggs*/\nham", "spam\n\nham;"),
        ("spam /*eggs*/\nham", "spam \nham;"),
        ("spam\n/*eggs*/ham", "spam\nham;"),
        ("spam /* eggs */ ham", "spam  ham;"),
        ("spam /* /* eggs */ */ ham", "spam  ham;"),
        ("spam /*/*/* eggs */*/*/ ham", "spam  ham;"),
        ("spam\n/*/*/* eggs */*/*/\nham", "spam\n\nham;"),
        ("spam /* eggs */ ham", "spam  ham;"),
    ],
)
def test_parsing_remove_multilines(inputs, outputs, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert s.parsed[0] == outputs


@pytest.mark.parametrize(
    "inputs, outputs",
    [
        ("spam /* eggs */*/ ham", "spam */ ham;"),
        ("spam /* eggs */*/*/ ham", "spam */*/ ham;"),
        ("spam /*/* eggs */*/*/ ham", "spam */ ham;"),
        ("spam /*/* eggs */ ham", "spam /* ham;"),
        ("spam /*/*/* eggs */ ham", "spam /*/* ham;"),
        ("spam /*/*/* eggs */*/ ham", "spam /* ham;"),
    ],
)
def test_parsing_nested_multilines(inputs, outputs, secrets):
    s = Script(inputs, channel=Channel(**secrets["sql"]))
    assert s.parsed[0] == outputs


def test_large_query(secrets):
    query = """
            select spam from /*vikings.breakfast;
            -- eat all the spam before the vikings
            GO
            create plate as select * from the larder
            wait what*/
            breakfast
            where deliciousness > 9;
            go ;
            and on;
            go;
            and on;
    """
    cleaned_expected = [
        "select spam from breakfast where deliciousness > 9;",
        "and on;",
        "and on;",
    ]
    q = Script(query, channel=Channel(**secrets["sql"]))
    assert cleanup_whitespace(q.parsed) == cleaned_expected


@pytest.mark.mssql
@pytest.mark.xfail
def test_errors_being_swallowed(secrets):
    raw = """
    use IRISpii;

    select * from linkage.sodifjsd;

    if object_id('IRISpii.linkage.setup_for_reparsing') is not null drop table IRISpii.linkage.setup_for_reparsing;

    CREATE TABLE [linkage].[setup_for_reparsing](
        [display_id] [int] NULL,
        [new_emp_number] [varchar](200) NULL,
        [last_name] [varchar](50) NULL,
        [first_name] [varchar](50) NULL,
        [middle_name] [varchar](50) NULL,
        [full_name] [varchar](200) NOT NULL
    ) ON [PRIMARY];

    with fulled as (
        select
            *,
            concat(rtrim(replace(emp_last_name, ',', '')), ', ', rtrim(emp_first_name), ' '+rtrim(middle_name)) as full_name
        from linkage.sdaoifjs
    )
    insert into linkage.setup_for_reparsing (display_id, new_emp_number, last_name, first_name, middle_name, full_name)
    select * from fulled;

    go """
    with pytest.raises(Exception):
        Script(raw, channel=Channel(**secrets["sql"])).execute()

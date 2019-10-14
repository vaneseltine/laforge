import re

import pandas as pd
import pytest
from hypothesis import given, settings, strategies

from laforge.sql import (
    Channel,
    Identifier,
    Script,
    SQLChannelNotFound,
    SQLIdentifierProblem,
    SQLTableNotFound,
    Table,
    execute,
    is_reserved_word,
)


class TestVariousTableFeatures:
    def t_fix_bad_columns(self, arbitrary_table):
        has_blank_col = pd.DataFrame([1, 7, 0, 1], columns=[""])
        assert has_blank_col.columns == [""]
        arbitrary_table.write(has_blank_col)
        result = arbitrary_table.read()
        assert [str(x) for x in result.columns] != [""]

    def t_write_blank_df(self, arbitrary_table):
        blank_df = pd.DataFrame([])
        with pytest.raises(RuntimeError):
            arbitrary_table.write(blank_df)

    @pytest.mark.parametrize("incoming", [0, None, 64, "Engage."])
    def t_write_non_df(self, incoming, arbitrary_table):
        with pytest.raises(RuntimeError):
            arbitrary_table.write(incoming)

    def t_weird_in_and_out(self, weird_df, arbitrary_table):
        arbitrary_table.write(weird_df)
        result = arbitrary_table.read()
        # print(weird_df.dtypes, '\n', result.dtypes)
        diff = result.values == weird_df.values
        assert diff.all()


class TestChannel:
    def t_empty_blind_execute_fails(self, tmpdir):
        with pytest.raises(SQLChannelNotFound):
            _ = Channel.grab()
        with pytest.raises(SQLChannelNotFound):
            execute("select 1;")

    def t_blind_execute_with_one_channel(self, tmpdir):
        c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
        assert Channel.grab() == c1
        execute("select 1;")

    def t_blind_grab_the_latest(self, tmpdir):
        c1 = Channel(distro="sqlite", database=tmpdir / "c1.db")
        c2 = Channel(distro="sqlite", database=tmpdir / "c2.db")
        c3 = Channel(distro="sqlite", database=tmpdir / "c3.db")
        assert (c1 != c2) and (c1 != c3) and (c2 != c3)
        assert Channel.grab() == c3

    def t_same_spec_yields_same_channel(self, tmpdir):
        assert len(Channel.known_channels) == 0
        _ = Channel(distro="sqlite", database=tmpdir / "c1.db")
        _ = Channel(distro="sqlite", database=tmpdir / "c1.db")
        assert len(Channel.known_channels) == 1


class TestExecutions:

    very_simple = {
        "mssql": "select top 5 1 from information_schema.tables;",
        "sqlite": "select 1, 2 from sqlite_master;",
    }

    @pytest.mark.parametrize("fetch", ["df", "tuples", False])
    def t_try_to_fetch_bad_statements(self, test_channel, fetch):
        nonsense = "select aoweifjwo from wagurgugbbb;"
        with pytest.raises(Exception):
            test_channel.execute_statement(nonsense, fetch=fetch)
        with pytest.raises(Exception):
            execute(nonsense, fetch=fetch, channel=test_channel)

    @pytest.mark.parametrize("quote_ch", ["'", '"', ""])
    @pytest.mark.parametrize("fetch", ["df", "tuples", False])
    def t_fetch_good_statements(self, test_channel, test_distro, fetch, quote_ch):
        statement = quote_ch + self.very_simple[test_distro] + quote_ch
        test_channel.execute_statement(statement, fetch=fetch)
        execute(statement, fetch=fetch, channel=test_channel)


class TestFinding:
    def t_create_objects_via_shared_channel(self, test_channel):
        s = Script("select * from spam;", channel=test_channel)
        t = Table("spam", channel=test_channel)
        assert s.channel == t.channel == test_channel

    def t_channel_finds_created_tables(self, test_channel, medium_df):
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

    def t_channel_does_not_find_dropped_tables(self, test_channel, medium_df):
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


class TestIdentifier:
    @pytest.mark.parametrize("name", Identifier.WHITELIST)
    def t_whitelist(self, name):
        ident = Identifier(name, extra="xx")

        assert name == ident.normalized
        assert ident.check()

    # @pytest.mark.parametrize("name", Identifier.BLACKLIST)
    @pytest.mark.parametrize("name", ["?column?"])
    def t_blacklist(self, name):
        ident = Identifier(name, extra="xx")

        assert name != ident.normalized
        assert not ident.check()
        # assert Identifier(name, extra="0").normalized != name
        # assert Identifier(name).check()


class TestIdentifierNormalization:
    @pytest.mark.parametrize(
        "incoming, norm",
        [
            ("spam", "spam"),
            ("spam123", "spam123"),
            ("spam$123", "spam$123"),
            ("spam@123", "spam@123"),
            ("spam#123", "spam#123"),
            ("spam_123", "spam_123"),
            ("spam 123 egg", "spam_123_egg"),
            (" spam 123", "spam_123"),
            ("  spam 123", "spam_123"),
            ("spam 123 ", "spam_123"),
            ("spam 123  ", "spam_123"),
            ("spam!%^&*(){}+", "spam"),
            ("!%^&*(){}+spam", "spam"),
            ("spam------123", "spam_123"),
            ("spam _ ! 123", "spam___123"),
            ("!spam", "spam"),
            ("!&*spam", "spam"),
            ("1spam", "spam"),
            ("9822spam", "spam"),
            ("$spam", "spam"),
            ("2 a", "a"),
            ("a 2 2a a2 2", "a_2_2a_a2_2"),
            ("2 a 2 2a a2 2", "a_2_2a_a2_2"),
            ("#spam", "#spam"),
            ("_spam", "_spam"),
            ("spam", "spam"),
            ("@spam", "@spam"),
            ("__spam", "__spam"),
            ("spam__", "spam__"),
            ("__spam__", "__spam__"),
            ("SPAM_EGG", "SPAM_EGG"),
            ("SpamEgg", "SpamEgg"),
        ],
    )
    def t_basic(self, incoming, norm):
        assert Identifier(incoming).normalized == norm

    @pytest.mark.parametrize("incoming", ("spamegg" * 12, "spamegg" * 42))
    def t_truncate(self, incoming):
        assert len(Identifier(incoming).normalized) < len(incoming)

    @pytest.mark.parametrize(
        "incoming",
        [
            ("else"),
            ("cardinality"),
            ("octet_length"),
            ("xmlexists"),
            ("AUTHORIZATION"),
            ("foobarbaz" * 29),
        ],
    )
    def t_bad_names_change_and_produce_log_output(self, caplog, incoming):
        # 0 NOTSET; 10 DEBUG; 20 INFO; 30 WARNING; 40 ERROR; 50 CRITICAL
        caplog.set_level(1)
        assert str(incoming) != str(Identifier(incoming))
        assert caplog.text

    @pytest.mark.parametrize("n", [1245, "1234"])
    def t_bad_names_without_extra_are_manageable(self, n):
        _ = Identifier(n, extra=None).normalized

    @pytest.mark.parametrize("n", [None, ""])
    def t_non_names_without_extra_produce_exceptions(self, n):
        with pytest.raises(ValueError):
            Identifier(n, extra=None).normalized

    @pytest.mark.parametrize(
        "column_in, extra, column_out",
        [
            ("spam", 0, "spam"),
            ("spam", 1, "spam"),
            ("spam", 99, "spam"),
            ("", 0, "column_0"),
            ("", 1, "column_1"),
            ("", 2, "column_2"),
            ("0", 0, "column_0"),
            ("1", 0, "column_1"),
            ("2", 0, "column_2"),
            ("1", 1, "column_1"),
            ("2", 2, "column_2"),
        ],
    )
    def t_forced_normalization(self, extra, column_in, column_out):
        assert Identifier(column_in, extra=extra).normalized == column_out

    @given(
        incoming=strategies.from_regex(
            regex=r"[A-Za-z@_#][A-Za-z0-9@_#$]*", fullmatch=True
        )
    )
    def t_valid_identifiers_are_untouched(self, incoming):
        assert (Identifier(incoming).normalized == incoming) or is_reserved_word(
            incoming
        )


class TestScriptResults:
    def t_real_query_with_bad_columns(self, test_channel, test_distro, caplog):
        stmt = {
            "mssql": "select top 5 1 from information_schema.tables;",
            "sqlite": "select 1, 2 from sqlite_master;",
        }[test_distro]

        df = Script(stmt, channel=test_channel).to_table()
        # Builtin SQL drivers return bad column names (blank or '?column?')
        assert "WARNING" in caplog.text
        assert len(df.columns) > 0
        # and there should be no bad columns in the final set
        assert not set(Identifier.BLACKLIST).intersection(df.columns)
        # FYI, this is exactly what this should look like for mssql
        # result = list(tuple(x) for x in df.to_records())
        # assert result == [(0, 1, 2), (1, 1, 2), (2, 1, 2), (3, 1, 2), (4, 1, 2)]


class TestScriptActivation:

    simple_statements = ["select 1;", "select 1;\n go \n select 1;"]

    @pytest.mark.parametrize("stmt", simple_statements)
    def t_execute_with_channel_spec(self, test_channel, stmt):
        Script(stmt, channel=test_channel).execute()

    @pytest.mark.parametrize("stmt", simple_statements)
    def t_execute_without_channel_spec(self, test_channel, stmt):
        Script(stmt).execute()

    @pytest.mark.parametrize("stmt", simple_statements)
    def t_execute_read(self, test_channel, stmt):
        Script(stmt).read()

    @pytest.mark.parametrize("stmt", simple_statements)
    def t_execute_to_table(self, test_channel, stmt):
        Script(stmt).to_table()


class TestScriptParsing:
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
    def t_strip_semis(self, semi, gogo):
        s = "select 1 from sys.tables" + semi + gogo
        assert Script._normalize_batch_end(s) == "select 1 from sys.tables;"

    @pytest.mark.parametrize(
        "s", ["select 1 from sys.i_love_lego", "select 1 from sys.i_love_lego;"]
    )
    def t_do_not_get_too_angry_at_go(self, s):
        assert "go" in Script._normalize_batch_end(s)

    def t_q_parsing(self, test_channel):
        q = Script("select * from hi.there;", channel=test_channel)
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
    def t_query_parsing_go(self, inputs, cleaned_expected, test_channel):
        s = Script(inputs, channel=test_channel)
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
    def t_query_parsing_ignoring_comments(self, inputs, cleaned_expected, test_channel):
        s = Script(inputs, channel=test_channel)
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
    def t_comments_proper_double_dash(self, inputs, outputs, test_channel):
        s = Script(inputs, channel=test_channel)
        assert s.parsed == outputs

    @pytest.mark.parametrize(
        "inputs, outputs",
        [
            ("spam and eggs - eggs", ["spam and eggs - eggs;"]),
            ("spam and eggs - - sausage", ["spam and eggs - - sausage;"]),
        ],
    )
    def t_parsing_ignore_non_double_dash(self, inputs, outputs, test_channel):
        s = Script(inputs, channel=test_channel)
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
    def t_parsing_remove_multilines(self, inputs, outputs, test_channel):
        s = Script(inputs, channel=test_channel)
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
    def t_parsing_nested_multilines(self, inputs, outputs, test_channel):
        s = Script(inputs, channel=test_channel)
        assert s.parsed[0] == outputs

    def t_large_query(self, test_channel):
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
        q = Script(query, channel=test_channel)
        assert cleanup_whitespace(q.parsed) == cleaned_expected


def cleanup_whitespace(result):
    return [collapse_whitespace_TEST(q) for q in result]


def collapse_whitespace_TEST(s):
    result = s
    result = re.sub(r"[\n\s ]+", " ", result)
    result = result.strip()
    result = re.sub(" +;", ";", result)
    return result


iso_table_names = strategies.from_regex(regex=r"[A-Za-z_][A-Za-z0-9_]+", fullmatch=True)


class TestTable:
    def t_get_back_info(self, test_channel):
        name = "enterprise"
        t = Table(name, channel=test_channel)
        assert t.identifiers == {
            "name": name,
            "database": test_channel.database,
            "server": test_channel.server,
            "schema": test_channel.schema,
        }
        assert name in t.resolve()

    def t_resolve(self, arbitrary_table):
        assert arbitrary_table.resolve()
        with pytest.raises(Exception):
            arbitrary_table.resolve(strict=True)

    @pytest.mark.slow
    @given(incoming=iso_table_names)
    @settings(max_examples=50, deadline=None)
    def t_sql_iso_standard_table_name(self, incoming, minimal_df, test_channel):
        t = Table(f"{incoming}", channel=test_channel)
        if t.exists():
            return None
        try:
            t.write(minimal_df)
        finally:
            t.drop(ignore_existence=True)

    def t_drop_mechanics(self, minimal_df, arbitrary_table):
        t = arbitrary_table
        t.write(minimal_df)
        t.drop(ignore_existence=True)
        with pytest.raises(SQLTableNotFound):
            t.drop(ignore_existence=False)
        t.write(minimal_df)
        t.drop(ignore_existence=False)
        t.drop(ignore_existence=True)

    def t_row_count(self, arbitrary_table, minimal_df):
        t = arbitrary_table
        t.write(minimal_df)
        assert len(t) == len(minimal_df) > 0

    def t_insufficient_identifiers(self, test_channel):
        with pytest.raises(SQLIdentifierProblem):
            _ = Table("", channel=test_channel)


class TestReservedWords:
    @pytest.mark.parametrize(
        "keyword",
        [
            "close",
            "del",
            "elif",
            "else",
            "lambda",
            "nonlocal",
            "numeric",
            "privileges",
            "row",
            "string",
            "table",
            "time",
            "view",
            "yield",
        ],
    )
    def t_reserved(self, keyword):
        assert is_reserved_word(keyword)
        assert is_reserved_word(keyword.lower())
        assert is_reserved_word(keyword.title())
        assert is_reserved_word(keyword.upper())

    @pytest.mark.parametrize(
        "keyword",
        [
            "Darmok",
            "Jalad",
            "Shaka",
            "Sokath",
            "Tanagra",
            "Temarc",
            "Temba",
            "Uzani",
            1701,
            None,
        ],
    )
    def t_non_reserved(self, keyword):
        assert not is_reserved_word(keyword)
        if isinstance(keyword, str):
            assert not is_reserved_word(keyword.lower())
            assert not is_reserved_word(keyword.title())
            assert not is_reserved_word(keyword.upper())

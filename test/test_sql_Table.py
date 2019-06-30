import pytest
from hypothesis import given, settings, strategies
from laforge.sql import SQLIdentifierProblem, SQLTableNotFound, Table

iso_table_name_generation = strategies.from_regex(
    regex=r"[A-Za-z_][A-Za-z0-9_]+", fullmatch=True
)


@pytest.mark.slow
@given(incoming=iso_table_name_generation)
@settings(max_examples=50, deadline=None)
def test_sql_iso_standard_table_name(incoming, unimportant_df, test_channel):
    t = Table(f"{incoming}", channel=test_channel)
    if t.exists():
        return None
    try:
        t.write(unimportant_df)
    finally:
        t.drop(ignore_existence=True)


def test_drop_mechanics(unimportant_df, arbitrary_table):
    t = arbitrary_table
    t.write(unimportant_df)
    t.drop(ignore_existence=True)
    with pytest.raises(SQLTableNotFound):
        t.drop(ignore_existence=False)
    t.write(unimportant_df)
    t.drop(ignore_existence=False)
    t.drop(ignore_existence=True)


def test_row_count(arbitrary_table, unimportant_df):
    t = arbitrary_table
    t.write(unimportant_df)
    assert len(t) == len(unimportant_df) > 0


def test_insufficient_identifiers(test_channel):
    with pytest.raises(SQLIdentifierProblem):
        _ = Table("", channel=test_channel)

#!/usr/bin/env python3
"""
unit tests

see: py.test --fixtures
"""

import pytest
from hypothesis import given, strategies, settings

from laforge.sql import SQLTableNotFound, Table, SQLIdentifierProblem


CANONICAL_DISTROS = ["mssql", "mysql", "postgresql", "sqlite"]


@pytest.mark.parametrize("distro", CANONICAL_DISTROS)
def test_temp_table_creation(make_temp_table, unimportant_df, distro):
    t = make_temp_table("sql")
    t.write(unimportant_df)
    assert t.exists()


@pytest.mark.parametrize("distro", CANONICAL_DISTROS)
def test_drop_mechanics(make_temp_table, unimportant_df, distro):
    t = make_temp_table(distro)
    t.write(unimportant_df)
    t.drop(ignore_existence=True)
    with pytest.raises(SQLTableNotFound):
        t.drop(ignore_existence=False)
    t.write(unimportant_df)
    t.drop(ignore_existence=False)
    t.drop(ignore_existence=True)


@pytest.mark.parametrize("distro", CANONICAL_DISTROS)
def test_row_count(make_temp_table, unimportant_df, distro):
    t = make_temp_table(distro)
    t.write(unimportant_df)
    assert len(t) == len(unimportant_df) > 0


# as per SQL ISO standard
iso_table_name_generation = strategies.from_regex(
    regex=r"[A-Za-z_][A-Za-z0-9_]+", fullmatch=True
)


@pytest.mark.slow
@given(incoming=iso_table_name_generation)
@settings(max_examples=50, deadline=None)
def test_iso_table_name_generation_sqlite(make_channel, minimal_df, incoming):
    distro = "sqlite"
    t = Table(f"{incoming}", channel=make_channel(distro))
    if t.exists():
        return None
    try:
        t.write(minimal_df)
    finally:
        t.drop(ignore_existence=True)


@pytest.mark.slow
@pytest.mark.postgresql
@given(incoming=iso_table_name_generation)
@settings(max_examples=50, deadline=None)
def test_iso_table_name_generation_postgresql(make_channel, minimal_df, incoming):
    distro = "postgresql"
    t = Table(f"{incoming}", channel=make_channel(distro))
    if t.exists():
        return None
    try:
        t.write(minimal_df)
    finally:
        t.drop(ignore_existence=True)


@pytest.mark.slow
@pytest.mark.mysql
@given(incoming=iso_table_name_generation)
@settings(max_examples=50, deadline=None)
def test_iso_table_name_generation_mysql(make_channel, minimal_df, incoming):
    distro = "mysql"
    t = Table(f"{incoming}", channel=make_channel(distro))
    if t.exists():
        return None
    try:
        t.write(minimal_df)
    finally:
        t.drop(ignore_existence=True)


@pytest.mark.slow
@pytest.mark.mssql
@given(incoming=iso_table_name_generation)
@settings(max_examples=50, deadline=None)
def test_iso_table_name_generation_mssql(make_channel, minimal_df, incoming):
    distro = "mssql"
    t = Table(f"{incoming}", channel=make_channel(distro))
    if t.exists():
        return None
    try:
        t.write(minimal_df)
    finally:
        t.drop(ignore_existence=True)


POS_NAME = [("spam"), ("[spam]")]
POS_NAME_SCHEMA = [
    ("breakfast.spam"),
    ("[breakfast].spam"),
    ("breakfast.[spam]"),
    ("[breakfast].[spam]"),
]
POS_NAME_SCHEMA_DATABASE = [
    ("camelot.breakfast.spam"),
    ("[camelot].[breakfast].[spam]"),
]
POS_ALL = [("MPFC.camelot.breakfast.spam"), ("[MPFC].[camelot].[breakfast].[spam]")]

POSITIONAL_CONFIGS = POS_NAME + POS_NAME_SCHEMA + POS_NAME_SCHEMA_DATABASE + POS_ALL

KEYWORD_CONFIGS = [({"schema": "breakfast", "database": "camelot", "server": "MPFC"},)]


def fake_channel():
    pass


def fake_distro():
    pass


fake_channel.metadata = "moo"
fake_channel.distro = fake_distro
fake_channel.server = "MPFC"
fake_channel.database = "camelot"
fake_channel.schema = "breakfast"
fake_distro.untouchable_identifiers = []
fake_distro.minimal_keywords = []


def test_insufficient_identifiers():
    with pytest.raises(SQLIdentifierProblem):
        _ = Table("", channel=fake_channel)


# @pytest.mark.parametrize("arg", POSITIONAL_CONFIGS)
# def test_identifiers(arg):
#     table = Table(arg, channel=fake_channel)
#     assert table.name == "spam"
#     assert all(
#         str(getattr(table, k))
#         == str(getattr(fake_channel, k))
#         == str(mssql_test_info[k])
#         for k in mssql_test_info
#     )


# @pytest.mark.parametrize("arg", POSITIONAL_CONFIGS)
# def test_table_identifiers_are_immutable(arg):
#     t = Table(arg, channel=fake_channel)
#     cache_hash = hash(t)
#     with pytest.raises(AttributeError):
#         t.identifiers = {}
#     with pytest.raises(AttributeError):
#         t.name = "spam"
#     with pytest.raises(AttributeError):
#         t.schema = "spam"
#     with pytest.raises(AttributeError):
#         t.database = "spam"
#     with pytest.raises(AttributeError):
#         t.server = "spam"
#     t.identifiers["name"] = "rotten_meat"
#     assert t.identifiers["name"] != "rotten_meat"
#     assert hash(t) == cache_hash


# @pytest.mark.parametrize("arg", POSITIONAL_CONFIGS)
# def test_resolve(arg):
#     table = Table(arg, channel=fake_channel)
#     assert table.resolve() == "[camelot].[breakfast].[spam]"


# @pytest.mark.parametrize("arg", POS_NAME_SCHEMA_DATABASE)
# @pytest.mark.parametrize("kwargs", [{"schema": "breakfast"}, {"database": "camelot"}])
# def test_resolve_identifiers_with_kws(arg, kwargs):
#     table = Table(arg, **kwargs, channel=fake_channel)
#     assert all(
#         table.identifiers[key] == mssql_test_info[key]
#         for key in ["server", "database", "schema"]
#     )


# @pytest.mark.parametrize(
#     "kwargs",
#     [
#         {"schema": "lunch"},
#         {"database": "camenotverymuch"},
#         {"schema": "lunch"},
#         {"database": "camenotverymuch"},
#         {"schema": "lunch", "database": "camenotverymuch"},
#         {"schema": "lunch", "database": "camenotverymuch"},
#     ],
# )
# def test_string_overwrites_kwargs_to_good_effect(kwargs):
#     table = Table("camelot.breakfast.spam", **kwargs, channel=fake_channel)
#     assert all(
#         table.identifiers[key] == mssql_test_info[key]
#         for key in ["server", "database", "schema"]
#     )


# @pytest.mark.parametrize(
#     "arg",
#     [
#         "camelot.lunch.spam",
#         "camenotverymuch.breakfast.spam",
#         "camenotverymuch.lunch.spam",
#     ],
# )
# def test_string_overwrites_kwargs_to_ill_effect(arg):
#     table = Table(arg, schema="breakfast", database="camelot", channel=fake_channel)
#     assert not all(
#         table.identifiers[key] == mssql_test_info[key]
#         for key in ["server", "database", "schema"]
#     )

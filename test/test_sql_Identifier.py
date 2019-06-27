#!/usr/bin/env python3
"""
unit tests

see: py.test --fixtures
"""
import pytest


from laforge.sql import Identifier
from laforge import toolbox

from hypothesis import given, strategies


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
def test_norm_id(incoming, norm):
    assert Identifier(incoming).normalized == norm


@pytest.mark.parametrize("incoming", ("spamegg" * 12, "spamegg" * 42))
def test_norm_id_truncate(incoming):
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
def test_norm_id_issues_any_log(caplog, incoming):
    # 0 NOTSET; 10 DEBUG; 20 INFO; 30 WARNING; 40 ERROR; 50 CRITICAL
    caplog.set_level(1)
    assert str(incoming) != str(Identifier(incoming))
    assert caplog.text


@pytest.mark.parametrize("n", [1245, "", "&&&", "$$$", "1234"])
def test_norm_id_without_extra_means_exceptions(n):
    with pytest.raises(ValueError):
        _ = Identifier(n, extra=None).normalized


def test_norm_id_ignore_None():
    _ = Identifier(None, extra=None).normalized


@pytest.mark.parametrize(
    "in_int, in_col, out_col",
    [
        (0, "spam", "spam"),
        (1, "spam", "spam"),
        (99, "spam", "spam"),
        (0, "", "column_0"),
        (1, "", "column_1"),
        (2, "", "column_2"),
        (0, "0", "column_0"),
        (0, "1", "column_1"),
        (0, "2", "column_2"),
        (1, "1", "column_1"),
        (2, "2", "column_2"),
    ],
)
def test_forced_normalization(in_int, in_col, out_col):
    assert Identifier(in_col, extra=in_int).normalized == out_col


@given(
    incoming=strategies.from_regex(regex=r"[A-Za-z@_#][A-Za-z0-9@_#$]*", fullmatch=True)
)
def test_basic_valid_identifiers(incoming):
    assert (Identifier(incoming).normalized == incoming) or toolbox.is_reserved_word(
        incoming
    )

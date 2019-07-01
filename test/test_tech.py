# import pytest

from laforge.tech import Technobabbler
from laforge.command import technobabble
from time import time


def test_technobabble_does_not_just_break():
    for _ in range(100):
        technobabble(Technobabbler)


def test_technobabble_no_longer_than_twenty_milliseconds():
    for _ in range(10):
        start = time()
        technobabble(Technobabbler)
        elapsed = time() - start
        assert elapsed <= 0.02


def test_technobabble_prints_match(capsys):  # or use "capfd" for fd-level
    technobabble(Technobabbler, match="x")
    captured = capsys.readouterr()
    assert "x" in captured.out.lower()
    assert not captured.err


def test_technobabble_does_not_crash(capsys):
    technobabble(Technobabbler, match="zzzzz")
    captured = capsys.readouterr()
    assert not captured.err

# import pytest

from laforge.tech import nobabble
from time import time


def test_technobabble_does_not_just_break():
    for _ in range(100):
        nobabble()


def test_technobabble_takes_less_than_ten_milliseconds():
    for _ in range(10):
        start = time()
        nobabble()
        assert (time() - start) < 0.01


def test_technobabble_prints_match(capsys):  # or use "capfd" for fd-level
    nobabble(match="x")
    captured = capsys.readouterr()
    assert "x" in captured.out
    assert not captured.err


def test_technobabble_does_not_crash(capsys):
    nobabble(match="zzzzz")
    captured = capsys.readouterr()
    assert not captured.err

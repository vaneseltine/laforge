# import pytest

from laforge.tech import Technobabbler
from laforge.command import technobabble
from time import time


def test_technobabble_does_not_just_break():
    for _ in range(100):
        technobabble(Technobabbler)


def test_technobabble_takes_less_than_ten_milliseconds():
    for _ in range(10):
        start = time()
        technobabble(Technobabbler)
        assert (time() - start) < 0.01


def test_technobabble_prints_match(capsys):  # or use "capfd" for fd-level
    technobabble(Technobabbler, match="x")
    captured = capsys.readouterr()
    assert "x" in captured.out.lower()
    assert not captured.err


def test_technobabble_does_not_crash(capsys):
    technobabble(Technobabbler, match="zzzzz")
    captured = capsys.readouterr()
    assert not captured.err

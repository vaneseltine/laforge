# import pytest

from laforge.tech import Technobabbler
from laforge.command import technobabble
from time import time


class TestTechnobabble:
    def t_does_not_just_break(self, trials=100):
        for _ in range(trials):
            technobabble(Technobabbler)

    def t_no_longer_than_twenty_milliseconds(self, trials=5):
        for _ in range(trials):
            start = time()
            technobabble(Technobabbler)
            elapsed = time() - start
            assert elapsed <= 0.02

    def t_prints_match(self, capsys):
        technobabble(Technobabbler, match="x")
        captured = capsys.readouterr()
        assert "x" in captured.out.lower()
        assert not captured.err

    def t_does_not_crash(self, capsys):
        technobabble(Technobabbler, match="zzzzz")
        captured = capsys.readouterr()
        assert not captured.err

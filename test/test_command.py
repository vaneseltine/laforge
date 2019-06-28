# import pytest

from laforge.tech import nobabble
from time import time


def test_technobabble_does_not_break():
    for _ in range(100):
        nobabble()


def test_technobabble_takes_less_than_ten_milliseconds():
    start = time()
    nobabble(n=10)
    assert (time() - start) < 0.1

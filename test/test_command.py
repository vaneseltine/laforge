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

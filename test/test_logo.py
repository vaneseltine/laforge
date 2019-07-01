# import pytest

from laforge.logo import get_clickable


def test_logo_creation():
    clickable = get_clickable()
    for thing in ("laforge", "python"):
        assert thing in clickable.lower()

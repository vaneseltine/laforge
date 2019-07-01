import os

import pytest


def test_new_test_distro_fixture(test_distro):
    assert test_distro == os.environ.get("LFTEST_DISTRO", "sqlite")

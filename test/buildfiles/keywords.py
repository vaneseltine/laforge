def good_a():
    assert True


def bad_a():
    assert False


def good_b():
    assert True


def bad_b():
    assert False


def _never_good():
    assert False


def _never_run_bad():
    assert False

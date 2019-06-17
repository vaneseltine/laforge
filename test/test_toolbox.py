import pytest

from laforge.toolbox import verify_file_is_writable


def test_writable(tmpdir):
    writable_file = tmpdir / "harga's_house_of_ribs.txt"
    verify_file_is_writable(writable_file)


@pytest.mark.xfail(reason="Need to sort out how to run this.")
def test_unwritable(tmpdir):
    writable_file = tmpdir / "troll's_head_tavern.txt"
    with writable_file.open("a") as write_that:
        write_that.write("blah")
        with pytest.raises(PermissionError):
            verify_file_is_writable(writable_file)


from laforge.toolbox import flatten


@pytest.mark.parametrize(
    "incoming",
    [
        [()],
        ([]),
        [[[]]],
        ((())),
        [[[]], [[]]],
        ([[]], [[]]),
        ((()), [[[]]]),
        ([[], []], [[[((((((([[]])))))))]]]),
        ([[], [[]], [[[]]], [[[[]]]]]),
        (()),
    ],
)
def test_nothing_from_nothing_leaves_nothing(incoming):
    assert list(flatten(incoming)) == []


@pytest.mark.parametrize(
    "incoming, output",
    [
        ([2], [2]),
        ([[2], [3]], [2, 3]),
        ([[3, [4]], 6], [3, 4, 6]),
        ([4, [4], 4, [4], 4, [[4]], [[]]], [4, 4, 4, 4, 4, 4]),
    ],
)
def test_flatten_flattens(incoming, output):
    assert list(flatten(incoming)) == output


@pytest.mark.parametrize(
    "incoming, output",
    [
        (["spam"], ["spam"]),
        ([["spam"], ["eggs"]], ["spam", "eggs"]),
        ([["spam", ["eggs"]], "spam"], ["spam", "eggs", "spam"]),
        (
            ["spam", ["spam"], "spam", ["spam"], "spam", [["spam"]], [[]]],
            ["spam", "spam", "spam", "spam", "spam", "spam"],
        ),
    ],
)
def test_flatten_leaves_strings(incoming, output):
    assert list(flatten(incoming)) == output


from laforge.toolbox import is_reserved_word


@pytest.mark.parametrize(
    "kw",
    [
        "else",
        "table",
        "row",
        "privileges",
        "view",
        "string",
        "time",
        "numeric",
        "close",
    ],
)
def test_reserved_words(kw):
    assert is_reserved_word(kw)


@pytest.mark.parametrize("kw", ["moomoo", "meowmeow", "woofwoof", "barkbark", "bowwow"])
def test_non_reserved_words(kw):
    assert not is_reserved_word(kw)

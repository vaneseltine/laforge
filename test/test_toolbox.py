import pytest

from laforge.toolbox import flatten


class TestFlatten:
    @pytest.mark.parametrize(
        "incoming",
        [
            [],
            (),
            [[]],
            (()),
            [()],
            ([]),
            [[[]]],
            ((())),
            [[[]], [[]]],
            ([[]], [[]]),
            [([], [])],
            ((()), [[[]]]),
            ([[], []], [[[((((((([[]])))))))]]]),
            ([[], [[]], [[[]]], [[[[]]]]]),
        ],
    )
    def t_nothing_from_nothing_leaves_nothing(self, incoming):
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
    def t_flattens(self, incoming, output):
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
    def t_leaves_strings(self, incoming, output):
        assert list(flatten(incoming)) == output

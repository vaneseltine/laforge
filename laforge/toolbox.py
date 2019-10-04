""" Handful of utility functions

.. note:: These intentionally *only* depend on builtins.

.. note:: Some copyright information within this file is identified per-block below.
"""


def flatten(foo):
    """Take any set of nests in an iterator and reduce it into one generator.

    'Nests' include any iterable except strings.

    :param foo:

    .. note::

        :py:func:`flatten` was authored
        by `Amber Yust <https://stackoverflow.com/users/148870/amber>`_
        at https://stackoverflow.com/a/5286571. This function is not claimed
        under the laforge license.

    """
    # pylint: disable=invalid-name,blacklisted-name
    for x in foo:
        if hasattr(x, "__iter__") and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x

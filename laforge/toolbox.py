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


"""
Copyright 2019 Matt VanEseltine.

This file is part of laforge.

laforge is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

laforge is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with laforge.  If not, see <https://www.gnu.org/licenses/>.
"""

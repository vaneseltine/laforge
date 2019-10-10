""" Print the laforge logo. """

import sys
from collections import namedtuple
from pathlib import Path

LOGO = r"""
      __      ___      _______ _______ _____   _______ _______
     / /     /__ |    /______//______//____ \ /______//______/
    / /     __ | |   _______ __   __ _____/ /__ ____ _______
   / /     / / | |  / _____// /  / // _  __// //_  // _____/
  / /____ / /__| | / /     / /__/ // / \ \ / /__/ // /_____
 /______//_______|/_/     /______//_/  /_//______//_______/ """
LOGO = LOGO[1:]

RESET = "\033[0m"
MONOCHROME = sys.platform.startswith("win")

Color = namedtuple("Color", "red green blue")


def truecolor(red, green, blue, background):
    """ Produce an RGB color escape sequence to prepend strings in terminal.

    Thanks to Antti Haapala for this answer to an unrelated question:
    https://stackoverflow.com/a/45782972/7846185
    """
    return f"\033[{48 if background else 38};2;{red};{green};{blue}m"


def colorize(s, fore=None, back=None, monochrome=False):
    """ Add foreground and/or background color to a string. """
    if monochrome:
        return s
    forestring = truecolor(*fore, background=False) if fore else ""
    backstring = truecolor(*back, background=True) if back else ""
    colored = f"{RESET}{forestring}{backstring}{s}{RESET}"
    return colored


def get_version_display(*args, monochrome=MONOCHROME):
    from . import __version__

    items_to_combine = [
        (LOGO + f" {__version__}\n", Color(102, 204, 255)),
        (
            f"laforge {__version__} at {Path(__file__).parent.absolute()}",
            Color(127, 127, 127),
        ),
        (
            f"Python {sys.version.split(' ')[0]} at {sys.executable}",
            Color(127, 127, 127),
        ),
    ]
    combined = "\n".join(
        (
            colorize(s, fore=color, monochrome=monochrome)
            for s, color in items_to_combine
        )
    )
    return combined

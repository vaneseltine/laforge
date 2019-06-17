""" Print the laforge logo. """

import sys
from collections import namedtuple
from pathlib import Path
from typing import Optional

LOGO = """\
      __      ___      _______ _______ _____   _______ _______
     / /     /__ |    /______//______//___  \ /______//______/
    / /     __ | |   _______ __   __ ____/  /__ ____ _______
   / /     / / | |  / _____// /  / // _  __// //_  // _____/
  / /____ / /__| | / /     / /__/ // / \ \ / /__/ // /_____
 /______//_______|/_/     /______//_/  /_//______//_______/ """  # noqa

RESET = "\033[0m"

Color = namedtuple("Color", "red green blue")


def truecolor(red: int, green: int, blue: int, background: bool) -> str:
    """ Produce an RGB color escape sequence to prepend strings in terminal.

    Thanks to Antti Haapala for this answer to an unrelated question:
    https://stackoverflow.com/a/45782972/7846185
    """
    return f"\033[{48 if background else 38};2;{red};{green};{blue}m"


def colorize(s: str, fg: Optional[Color] = None, bg: Optional[Color] = None) -> str:
    """ Add foreground and/or background color to a string. """
    forestring = truecolor(*fg, background=False) if fg else ""
    backstring = truecolor(*bg, background=True) if bg else ""
    return f"{RESET}{forestring}{backstring}{s}{RESET}"


def print_fancy() -> None:
    print(colorize(LOGO, fg=Color(red=102, green=204, blue=255)))


def get_clickable() -> str:
    from . import __version__

    logo = colorize(LOGO + " %(version)s\n", fg=Color(102, 204, 255))
    lfline = colorize(
        f"laforge {__version__} at {Path(__file__).parent.absolute()}",
        fg=Color(127, 127, 127),
    )
    pyline = colorize(
        f"Python {sys.version.split(' ')[0]} at {sys.executable}",
        fg=Color(127, 127, 127),
    )

    return "\n".join((logo, lfline, pyline))


if __name__ == "__main__":
    print_fancy()

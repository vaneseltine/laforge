#!/usr/bin/env python3
"""A low-key build system for working with data."""

__version__ = "0.8.0dev0"

from .decoupage import read, write, execute, exist
from .command import build


def run():
    """Launch laforge command line tool."""
    import laforge.command

    laforge.command.run()

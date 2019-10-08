"""A low-key build system for working with data."""

__version__ = "0.8.0dev0"

from .command import build
from .garnish import exists, load, read, save, write
from .sql import Channel, Table, Script, execute


def run():
    """Launch laforge command line tool."""
    import laforge.command

    laforge.command.run()

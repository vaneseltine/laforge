#!/usr/bin/env python3
"""A low-key build system for working with data."""

from .__version import __version__


def run_laforge() -> None:
    """Launch laforge command line tool."""
    from laforge.command import run_cli

    run_cli()

#!/usr/bin/env python3
"""A low-key build system for working with data."""

__version__ = "0.1.3"


def run_laforge():
    """Launch laforge command line tool."""
    from laforge.command import run_cli

    run_cli()

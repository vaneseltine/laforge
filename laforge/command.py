#!/usr/bin/env python3
"""Command-line interface for laforge."""

import sys
from pathlib import Path

import click

from . import __doc__ as LF_DOCSTRING
from . import __version__ as LF_VERSION
from . import logo
from .runner import engage

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_LOG_FILE = "./laforge.log"


@click.command(context_settings=CONTEXT_SETTINGS, help=LF_DOCSTRING)
@click.option(
    "-i",
    "--include",
    help="Include only functions matching the given pattern. (default: '.')",
    metavar="<pattern>",
)
@click.option(
    "-x",
    "--exclude",
    help="Exclude functions matching the given pattern. (default: '^_')",
    metavar="<pattern>",
)
@click.option(
    "-l", "--list", "list_only", is_flag=True, help="List build plan and exit."
)
@click.option("--debug", default=False, is_flag=True)
@click.argument(
    "buildfile",
    type=click.Path(exists=True, resolve_path=True, dir_okay=True),
    default=Path("."),
)
@click.option(
    "--log",
    default=DEFAULT_LOG_FILE,
    type=click.Path(resolve_path=True, dir_okay=False),
    help=f"Log file for build process (default: {DEFAULT_LOG_FILE}).",
)
@click.version_option(version=LF_VERSION, message=logo.get_version_display())
def run(buildfile, debug, include, exclude, list_only, log):
    """Parse arguments as from CLI and execute buildfile"""

    try:
        buildfile = find_buildfile(buildfile)
    except FileNotFoundError as err:
        print(err)
        exit(1)

    build(
        buildfile,
        debug=debug,
        log=log,
        include=include,
        exclude=exclude,
        list_only=list_only,
    )
    exit(0)


def build(
    buildfile=None,
    log="./laforge.log",
    debug=False,
    include="",
    exclude="",
    list_only=False,
):
    if buildfile is None:
        # Allow call directly from a buildfile
        buildfile = sys.argv[0]
    buildfile = Path(buildfile).resolve()

    engage(
        buildfile=buildfile,
        log=log,
        debug=debug,
        include=include,
        exclude=exclude,
        list_only=list_only,
    )


def find_buildfile(path="."):
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist.")
    if path.is_file():
        return path
    _acceptable_globs = ["build*.py", "*laforge*.py"]
    build_files = []
    for fileglob in _acceptable_globs:
        build_files.extend(list(path.glob(fileglob)))
    if not build_files:
        globs = " or ".join(_acceptable_globs)
        raise FileNotFoundError(
            f"No laforge buildfile (e.g., {globs}) found in {path}."
        )
    if len(build_files) > 1:
        found = (str(x) for x in build_files)
        raise FileNotFoundError(
            "\n  ".join(("Multiple possible laforge buildfiles found:", *found))
        )
    return build_files[0]

#!/usr/bin/env python3
"""Command-line interface for laforge."""

import sys
from pathlib import Path

import click

from . import __doc__ as LF_DOCSTRING
from .logo import get_version_display
from .runner import engage

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
DEFAULT_LOG_FILE = "./laforge.log"
DEFAULT_GLOBS = ["build*.py", "*laforge*.py"]


def show_version(ctx, _param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_version_display())
    ctx.exit()


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
    type=click.Path(resolve_path=True, writable=True, dir_okay=False),
    help=f"Log file for build process (default: {DEFAULT_LOG_FILE}).",
)
@click.option(
    "-V",
    "--version",
    is_flag=True,
    callback=show_version,
    expose_value=False,
    is_eager=True,
)
@click.pass_context
def run(ctx, buildfile, debug, include, exclude, list_only, log):
    """Parse arguments as from CLI and execute buildfile

    ..todo :

        Raise exception as Click

    """

    try:
        buildfile = find_buildfile(buildfile)
    except FileNotFoundError as err:
        raise click.UsageError(err.args, ctx=ctx)

    log_path = Path(log)
    if not log_path.parent.exists():
        raise click.FileError(log, f"{log_path.parent} does not exist.")

    build(
        buildfile,
        debug=debug,
        log=log_path,
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
    build_files = []
    for fileglob in DEFAULT_GLOBS:
        build_files.extend(list(path.glob(fileglob)))
    if not build_files:
        globs = " or ".join(DEFAULT_GLOBS)
        raise FileNotFoundError(
            f"No laforge buildfile (e.g., {globs}) found in {path}."
        )
    if len(build_files) > 1:
        found = (str(x) for x in build_files)
        raise FileNotFoundError(
            "\n  ".join(("Multiple possible laforge buildfiles found:", *found))
        )
    return build_files[0]

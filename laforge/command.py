#!/usr/bin/env python3
"""Command-line interface for laforge."""

import os
import sys
from pathlib import Path

from .logo import get_version_display


def run(args=None):
    """Parse arguments as from CLI and execute buildfile

    .. todo:

        "--dry-run", "-n", default=False

    .. todo:

        "--loop", default=False

    .. todo:

        "--log=LOG"         default="laforge.log"
    """
    if args is None:
        args = sys.argv[1:]

    if args in (["-V"], ["--version"]):
        version_info()

    if set(args) & {"-h", "--help"}:
        usage_info()

    try:
        args.remove("--debug")
    except ValueError:
        debug = False
    else:
        debug = True

    try:
        buildfile = find_buildfile(" ".join(args))
    except FileNotFoundError as err:
        print(" ".join(["Error!", *err.args]))
        usage_info(exit_code=1)

    build(buildfile, debug=debug)
    exit(0)


def version_info():
    print(get_version_display())
    exit(0)


def usage_info(exit_code=0):

    usage = """Usage: laforge [OPTIONS] (PATH)...

    laforge: A low-key build system for working with data.

    Options
    -V, --version   Show the package version.
    -h, --help      Show this usage message.
    --debug         Increase logging.

    Path            Path for buildfile; default current dir."""

    print(usage)
    exit(exit_code)


def find_buildfile(path):
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
        found = "; ".join(str(x) for x in build_files)
        raise FileNotFoundError(f"Multiple possible laforge buildfiles found: {found}.")
    return build_files[0]


def build(buildfile=None, log="./laforge.log", debug=False, dry_run=False):
    if buildfile is None:
        # Allow call directly from a buildfile
        buildfile = sys.argv[0]
    buildfile = Path(buildfile).resolve()
    os.chdir(buildfile.parent)
    from .runner import engage

    engage(path=buildfile, log=log, debug=debug, dry_run=dry_run)

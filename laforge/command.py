#!/usr/bin/env python3
"""Command-line interface for laforge."""

import logging
import sys
import time
from pathlib import Path

from . import __doc__ as package_docstring
from . import logo

sys.argv = sys.argv[1:]


def run():
    print("hi")
    if not sys.argv:
        print("help")
        exit(0)
    if sys.argv[0] in ("-V", "--version"):
        print(logo.get_version_display())
        exit(0)
    buildfile = find_buildfile(" ".join(sys.argv))
    build(buildfile)


def find_buildfile(path):
    path = Path(path)
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
        raise FileExistsError(f"Multiple possible laforge buildfiles found: {found}.")
    return build_files[0]


# @click.command(help="Run an existing laforge buildfile.")
# @click.option("--debug", default=False, is_flag=True)
# @click.option("--dry-run", "-n", default=False, is_flag=True)
# @click.option("--loop", default=False, is_flag=True)
# @click.option(
#     "--log",
#     default="laforge.log",
#     type=click.Path(resolve_path=True, dir_okay=False),
#     help="Log build process at LOG.",
# )
def build(buildfile, log="./laforge.log", debug=False, dry_run=False, loop=False):
    from .builder import TaskList

    runs = 1 if not loop else 100
    for _ in range(runs):
        run_one_build(
            list_class=TaskList,
            script_path=Path(buildfile),
            log=Path(log),
            debug=debug,
            dry_run=dry_run,
        )
        if loop:
            response = input("\nEnter to rebuild, anything else to quit: ")
            if response:
                break
            print("")


def run_one_build(*, list_class, script_path, log, debug=False, dry_run=False):
    path = find_buildfile(script_path)

    start_time = time.time()
    # THEN set logging -- helps avoid importing pandas at debug level
    logger = get_package_logger(log, debug)

    logger.info("%s launched.", path)
    if debug:
        logger.debug("Debug mode is on.")

    task_list = list_class(path)
    if dry_run:
        task_list.dry_run()
        return
    task_list.execute()
    elapsed = round(time.time() - start_time, 2)
    logger.info("%s completed in %s seconds.", path, elapsed)


def get_package_logger(log_file, debug):
    noisiness = logging.DEBUG if debug else logging.INFO

    if noisiness == logging.DEBUG:
        formatter = logging.Formatter(
            fmt="{asctime} {name:<20} {lineno:>3}:{levelname:<7} | {message}",
            style="{",
            datefmt=r"%Y%m%d-%H%M%S",
        )
    else:
        formatter = logging.Formatter(
            fmt="{asctime} {levelname:>7} | {message}", style="{", datefmt=r"%H:%M:%S"
        )
    file_handler = logging.FileHandler(filename=log_file)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers = [file_handler, stream_handler]
    logging.basicConfig(level=logging.INFO, handlers=handlers)

    logging.getLogger().setLevel(noisiness)

    new_logger = logging.getLogger(__name__)
    new_logger.debug(f"Logging: {log_file}")
    return new_logger

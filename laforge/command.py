#!/usr/bin/env python3
"""Command-line interface for laforge."""

import logging
import sys
import time
from pathlib import Path
from pprint import pprint

import click

from . import __doc__ as package_docstring
from . import __version__ as package_version
from . import logo

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS, help=package_docstring)
@click.version_option(version=package_version, message=logo.get_version_display())
def run_cli():
    pass


@click.command(help="Build an existing laforge build INI.")
@click.argument(
    "ini", type=click.Path(exists=True, resolve_path=True, dir_okay=True), default="."
)
@click.option("--debug", default=False, is_flag=True)
@click.option("--dry-run", "-n", default=False, is_flag=True)
@click.option("--loop", default=False, is_flag=True)
@click.option(
    "--log",
    default="laforge.log",
    type=click.Path(resolve_path=True, dir_okay=False),
    help="Log build process at LOG.",
)
def build(ini, log="./laforge.log", debug=False, dry_run=False, loop=False):
    from .builder import TaskList

    runs = 1 if not loop else 100
    for _ in range(runs):
        run_build(
            list_class=TaskList,
            script_path=Path(ini),
            log=Path(log),
            debug=debug,
            dry_run=dry_run,
        )
        if loop:
            response = input("\nEnter to rebuild, anything else to quit: ")
            if response:
                break
            print("")


def run_build(*, list_class, script_path, log, debug=False, dry_run=False):
    path = find_build_config(script_path)

    start_time = time.time()
    logger = get_package_logger(log, debug)

    # THEN set logging -- helps avoid importing pandas at debug level

    logger.info("%s launched.", path)
    if debug:
        click.echo("Debug mode is on.")
    logger.debug("Debug mode is on.")

    task_list = list_class(path.read_text(), location=path.parent)
    if dry_run:
        task_list.dry_run()
    else:
        task_list.execute()
        elapsed = round(time.time() - start_time, 2)
        logger.info("%s completed in %s seconds.", path, elapsed)


def find_build_config(path):
    path = Path(path)
    if path.is_file():
        return path
    _acceptable_globs = ["build*.ini", "*laforge*.ini"]
    build_files = []
    for fileglob in _acceptable_globs:
        build_files.extend(list(path.glob(fileglob)))
    if not build_files:
        globs = " or ".join(_acceptable_globs)
        raise FileNotFoundError(f"No laforge INI (e.g., {globs}) found in {path}.")
    if len(build_files) > 1:
        found = "; ".join(str(x) for x in build_files)
        raise FileExistsError(f"Multiple possible laforge INIs found: {found}.")
    return build_files[0]


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


@click.command(hidden=True, help="Receive a quick engineering consultation.")
@click.option("-n", type=int, default=1, help="Receive N consultations.")
@click.option(
    "--match",
    type=str,
    default="",
    help="Try to receive consultation(s) including MATCH.",
)
def consult(n, match):
    from .tech import Technobabbler

    technobabble(Technobabbler, n, match)


def technobabble(babbler, n=1, match=None):
    for _ in range(n):
        if match:
            babble = babbler.find(match)
        else:
            babble = babbler().babble()
        click.echo(babble)


@click.command(help="Interactively create a new laforge build INI.")
@click.argument(
    "path",
    type=click.Path(writable=True, resolve_path=True, dir_okay=False),
    default=Path("./build.ini"),
)
def create(path):
    from .create_ini import create_ini

    return_code = create_ini(Path(path))
    if return_code == 0:
        click.echo(f"\nNew laforge INI written at: {path}\nEnjoy!")
    sys.exit(return_code)


@click.command(help="Describe the present build environment known to laforge.")
@click.argument("path", type=click.Path(), nargs=-1)
@click.option(
    "--no-warning",
    help="Do not display warning about cleartext.",
    default=False,
    is_flag=True,
    prompt="WARNING: Output may include passwords or keys stored as cleartext "
    + "in laforge build INIs, configs, or .envs. Continue?",
)
def env(no_warning=False, path=None):
    user_has_accepted_warning = no_warning
    if not user_has_accepted_warning:
        click.echo("Canceled.")
        return 1

    from .builder import show_env

    path = Path(" ".join(path) if path else ".")
    try:
        build_path = find_build_config(path)
    except FileNotFoundError:
        build_path = path

    result = show_env(build_path)
    click.echo("Constructed build environment:")
    pprint(result)  # noqa
    return 0


run_cli.add_command(build)
run_cli.add_command(consult)
run_cli.add_command(create)
run_cli.add_command(env)

if __name__ == "__main__":
    run_cli()

"""
Copyright 2019 Matt VanEseltine.

This file is part of laforge.

laforge is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

laforge is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with laforge.  If not, see <https://www.gnu.org/licenses/>.
"""

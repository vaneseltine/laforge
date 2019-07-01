#!/usr/bin/env python3
"""Command-line interface for laforge."""

from pathlib import Path
from pprint import pprint
import time
import logging
import sys

import click

from . import __doc__ as LF_DOCSTRING
from . import __version__ as LF_VERSION
from . import logo

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, help=LF_DOCSTRING)
@click.version_option(version=LF_VERSION, message=logo.get_version_display())
def run_cli():
    pass


@click.command(help="Build an existing laforge build INI.")
@click.argument(
    "ini", type=click.Path(exists=True, resolve_path=True, dir_okay=True), default="."
)
@click.option("--debug", default=False, is_flag=True)
@click.option("--dry-run", "-n", default=False, is_flag=True)
@click.option(
    "--log",
    default="laforge.log",
    type=click.Path(resolve_path=True, dir_okay=False),
    help="Log build process at LOG.",
)
def build(ini, log="./laforge.log", debug=False, dry_run=False):
    from .builder import TaskList

    run_build(
        list_class=TaskList,
        script_path=Path(ini),
        log=Path(log),
        debug=debug,
        dry_run=dry_run,
    )


def run_build(*, list_class, script_path, log, debug=False, dry_run=False):
    """laforge's core build command

    ..todo: TODO: move interactive portion to command.py"""
    path = Path(script_path)
    if path.is_dir():
        path = find_build_config_in_directory(path)

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
        elapsed = seconds_since(start_time)
        logger.info("%s completed in %s seconds.", path, elapsed)


def find_build_config_in_directory(path):
    """..todo: TODO: move interactive portion to command.py"""
    _acceptable_globs = ["build*.ini", "*laforge*.ini"]
    build_files = None
    for fileglob in _acceptable_globs:
        build_files = list(path.glob(fileglob))
        if build_files:
            break
    if not build_files:
        print(
            "ERROR: No laforge INI (e.g., {eg}) "
            "found in {dir}. ".format(dir=path, eg=(" or ".join(_acceptable_globs)))
        )
        exit(1)
    if len(build_files) > 1:
        print("ERROR: Must specify a laforge INI: {}".format(build_files))
        exit(1)
    return build_files[0]


def seconds_since(previous_time, round_to=2):
    """..todo: TODO: to command.py"""
    elapsed_raw = time.time() - previous_time
    if round_to:
        return round(elapsed_raw, round_to)
    return elapsed_raw


def get_package_logger(log_file, debug):
    """..todo: TODO: to command.py"""
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
        print(babble)


@click.command(help="Interactively create a new laforge build INI.")
@click.argument(
    "path",
    type=click.Path(writable=True, resolve_path=True, dir_okay=False),
    default=Path("./build.ini"),
)
def create(path):
    from .create_ini import create_ini

    create_ini(Path(path))


@click.command(help="Describe the build environment known to laforge.")
@click.argument("path", type=click.Path(), nargs=-1)
@click.option(
    "--no-warning",
    help="Do not display cleartext warning.",
    default=False,
    is_flag=True,
)
def env(path=None, no_warning=False):
    from .builder import show_env

    if user_confirms_cleartext(no_warning):
        path = Path(" ".join(path)) if path else None
        result = show_env(path=path)
        pprint(result)


def user_confirms_cleartext(no_warning):
    import PyInquirer as inq

    if no_warning:
        return True

    answers = inq.prompt(
        {
            "type": "confirm",
            "name": "continuing",
            "message": (
                "Output may include passwords or keys stored as cleartext "
                + "in laforge build INIs, configs, or .envs. Continue?"
            ),
            "default": False,
            "qmark": "WARNING:",
        },
        style=inq.style_from_dict(
            {inq.Token.QuestionMark: "#cd422d bold", inq.Token.Question: "#cd422d"}
        ),
    )
    return answers.get("continuing", False)


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

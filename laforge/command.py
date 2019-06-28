#!/usr/bin/env python3
"""Command-line interface for laforge."""

from pathlib import Path

import click

from . import __doc__ as LF_DOCSTRING
from . import __version__ as LF_VERSION
from . import logo

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS, help=LF_DOCSTRING)
@click.version_option(version=LF_VERSION, message=logo.get_clickable())
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
    from .builder import run_build

    run_build(script_path=Path(ini), log=Path(log), debug=debug, dry_run=dry_run)


@click.command(hidden=True, help="Receive a quick engineering consultation.")
@click.option("-n", type=int, default=1, help="Receive N consultations.")
@click.option(
    "--match",
    type=str,
    default="",
    help="Try to receive consultation(s) including MATCH.",
)
def consult(n, match):
    from . import tech

    tech.nobabble(n=n, match=match)


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
        show_env(path=path)


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

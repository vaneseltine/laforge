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
@click.option(
    "--log",
    default="laforge.log",
    type=click.Path(resolve_path=True, dir_okay=False),
    help="Path for log file.",
)
def run_cli(log: Path) -> None:
    pass


@click.command(help="Build an existing laforge build INI.")
@click.argument(
    "ini", type=click.Path(exists=True, resolve_path=True, dir_okay=True), default="."
)
@click.option("--debug", default=False, is_flag=True)
def build(ini: str, debug: bool) -> None:
    click.echo(f"Building {ini}")
    from .builder import run_build

    run_build(ini, debug)


@click.command(help="Interactively create a new laforge build INI.")
@click.argument(
    "ini",
    type=click.Path(writable=True, resolve_path=True, dir_okay=True),
    default="./build.ini",
)
@click.option("--debug", default=False, is_flag=True)
def create(ini: str, debug: bool) -> None:
    click.echo(f"Creating {ini}")
    from .create_ini import create_ini

    create_ini(ini, debug)


@click.command(hidden=True, help="Receive a quick engineering consultation.")
@click.option("-n", type=int, default=1, help="Number of responses.")
def consult(n: int) -> None:
    from .quarters import tech

    tech.nobabble(n=n)


run_cli.add_command(build)
run_cli.add_command(create)
run_cli.add_command(consult)

if __name__ == "__main__":
    run_cli()

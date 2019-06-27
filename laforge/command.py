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
    print(repr(ini))
    click.echo(f"Building {ini}")
    from .builder import run_build

    run_build(script_path=Path(ini), log=Path(log), debug=debug, dry_run=dry_run)


@click.command(help="Interactively create a new laforge build INI.")
@click.argument(
    "path",
    type=click.Path(writable=True, resolve_path=True, dir_okay=False),
    default=Path("./build.ini")
    # help="Write build INI to PATH.",
)
def create(path):
    click.echo(f"Creating {path}")
    from .create_ini import create_ini

    create_ini(Path(path))


@click.command(hidden=True, help="Receive a quick engineering consultation.")
@click.option("-n", type=int, default=1, help="receive N consultations")
@click.option(
    "--match", type=str, default="", help="receive consultation that includes 'MATCH'"
)
def consult(n, match):
    from .quarters import tech

    tech.nobabble(n=n, match=match)


run_cli.add_command(build)
run_cli.add_command(create)
run_cli.add_command(consult)

if __name__ == "__main__":
    run_cli()

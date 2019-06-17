""" Create a new build INI. """

import os
from datetime import datetime as dt
from pathlib import Path
from typing import Mapping, Union

import click
import PyInquirer as inq

from . import toolbox


def create_ini(path: str, debug: bool) -> None:
    # path = Path(path)

    path = receive_path()
    responses = receive_input(path.parent)
    output = create_output(responses)
    path.write_text(output)
    print("\nNew laforge INI written at: {path}\nEnjoy!")
    exit(0)


INQ_STYLE = inq.style_from_dict(
    {
        inq.Token.QuestionMark: "#7366ff bold",
        inq.Token.Answer: "#66ccff bold",
        inq.Token.Selected: "",  # defaults
        inq.Token.Instruction: "",
        inq.Token.Question: "",
    }
)


def receive_path():

    ini_questions = [
        {
            "type": "input",
            "name": "ini",
            "message": "Creating a new laforge INI at:",
            "default": "./build.ini",
        },
        {
            "type": "confirm",
            "name": "confirmed",
            "message": "This file exists. Okay to overwrite?",
            "default": False,
            "when": lambda a: Path(a["ini"]).exists(),
        },
    ]

    build_path = None
    while not build_path:
        ini_answers = inq.prompt(ini_questions, style=INQ_STYLE)
        confirmed = ini_answers.get("confirmed", True)
        if confirmed:
            build_path = Path(ini_answers["ini"]).resolve()
    click.echo(f"\nCreating {build_path}\n")
    return build_path


def receive_input(build_dir):
    DISTROS = {
        "Microsoft SQL Server": "mssql",
        "MySQL/MariaDB": "mysql",
        "PostgreSQL": "postgresql",
        "SQLite": "sqlite",
    }

    questions = [
        {
            "type": "input",
            "name": "read_dir",
            "message": f"Default read directory, relative to {build_dir}{os.sep}:",
            "default": "./",
        },
        {
            "type": "input",
            "name": "write_dir",
            "message": f"Default write directory, relative to {build_dir}{os.sep}:",
            "default": "./",
        },
        {
            "type": "input",
            "name": "execute_dir",
            "message": f"Default execute directory, relative to {build_dir}{os.sep}:",
            "default": "./",
        },
        {
            "type": "list",
            "name": "distro",
            "message": "SQL Distribution:",
            "choices": ["None"] + [*DISTROS.keys()],
            "filter": DISTROS.get,
        },
        {
            "type": "input",
            "name": "server",
            "message": "    Server:",
            "when": lambda a: a["distro"] in ("mssql", "mysql", "postgresql"),
        },
        {
            "type": "input",
            "name": "database",
            "message": "    Database:",
            "when": lambda a: a["distro"] in ("mssql", "mysql", "postgresql", "sqlite"),
        },
        {
            "type": "input",
            "name": "schema",
            "message": "    Schema:",
            "when": lambda a: a["distro"] in ("mssql"),
        },
    ]

    return inq.prompt(questions, style=INQ_STYLE)


def create_output(answers: Mapping) -> str:
    INTRO = ["# laforge configuration generated {}".format(dt.now()), "[DEFAULT]"]
    OUTTRO = ["\n[hello_world]", "SHELL: echo 'Hello, world!'", ""]
    output = INTRO
    for option, answer in answers.items():
        comment = "# " if not answer else ""
        output.append(f"{comment}{option}: {answer}")
    output.extend(OUTTRO)
    return "\n".join(output)

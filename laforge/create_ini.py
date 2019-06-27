""" Create a new build INI. """

import os
from datetime import datetime as dt
from pathlib import Path

import click
import PyInquirer as inq


def create_ini(path):
    path = receive_path(default=path)
    responses = receive_input(path.parent)
    output = create_output(path, responses)
    path.write_text(output)
    click.echo(f"\nNew laforge INI written at: {path}\nEnjoy!")
    exit(0)


INQ_STYLE = inq.style_from_dict(
    {
        inq.Token.QuestionMark: "#7366ff bold",
        inq.Token.Answer: "#66ccff bold",
        inq.Token.Selected: "#66ccff bold",
        inq.Token.Instruction: "",  # defaults
        inq.Token.Question: "",
    }
)


def receive_path(default):

    ini_questions = [
        {
            "type": "input",
            "name": "ini",
            "message": "Creating a new laforge INI at:",
            "default": str(default),
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
            build_path = ini_answers["ini"]
    click.echo(f"\nCreating {build_path}\n")
    return Path(build_path).resolve()


DISTROS = {
    "Microsoft SQL Server": "mssql",
    "MySQL/MariaDB": "mysql",
    "PostgreSQL": "postgresql",
    "SQLite": "sqlite",
}


def receive_input(build_dir):

    questions = [
        {
            "type": "input",
            "name": "read_dir",
            "message": f"Default read directory, relative to {build_dir}{os.sep}:",
            "default": f".{os.sep}",
        },
        {
            "type": "input",
            "name": "write_dir",
            "message": f"Default write directory, relative to {build_dir}{os.sep}:",
            "default": f".{os.sep}",
        },
        {
            "type": "input",
            "name": "execute_dir",
            "message": f"Default execute directory, relative to {build_dir}{os.sep}:",
            "default": f".{os.sep}",
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
            "when": lambda a: a["distro"] in ["mssql", "mysql", "postgresql"],
        },
        {
            "type": "input",
            "name": "database",
            "message": "    Database:",
            "when": lambda a: a["distro"] in ["mssql", "mysql", "postgresql", "sqlite"],
        },
        {
            "type": "input",
            "name": "schema",
            "message": "    Schema:",
            "when": lambda a: a["distro"] in ["mssql"],
        },
    ]

    return inq.prompt(questions, style=INQ_STYLE)


def create_output(path, answers):
    intro = [
        f"# laforge configuration generated at",
        f"# {path}",
        f"# {dt.now().strftime(r'%Y-%m-%d %H:%M:%S')}",
        "",
        "[DEFAULT]",
    ]
    outtro = ["\n[hello_world]", "SHELL: echo 'Hello, world!'", ""]
    output = intro
    for option, answer in answers.items():
        comment = "# " if not answer else ""
        output.append(f"{comment}{option}: {answer}")
    output.extend(outtro)
    return "\n".join(output)

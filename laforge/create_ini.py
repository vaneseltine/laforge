""" Create a new build INI. """

import os
from datetime import datetime as dt
from pathlib import Path

import PyInquirer as inq


DISTROS = {
    "Microsoft SQL Server": "mssql",
    "MySQL/MariaDB": "mysql",
    "PostgreSQL": "postgresql",
    "SQLite": "sqlite",
}


INQ_STYLE = inq.style_from_dict(
    {
        inq.Token.QuestionMark: "#7366ff bold",
        inq.Token.Answer: "#66ccff bold",
        inq.Token.Selected: "#66ccff bold",
        inq.Token.Instruction: "",  # defaults
        inq.Token.Question: "",
    }
)


def create_ini(path):
    path = receive_path(default=path)
    if not path:
        return 125
    responses = receive_input(path.parent)
    if not responses:
        return 125
    output = create_output(path, responses)
    path.write_text(output)
    return 0


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
            "when": lambda responses: Path(responses["ini"]).exists(),
        },
    ]

    while True:
        responses = inq.prompt(ini_questions, style=INQ_STYLE)
        # PyInquirer doesn't handle this quite how I'd prefer.
        # I can't simply distinguish between an unneeded confirmation
        # and a ctrl+c'd confirmation.
        #                       ini exists
        #                       yes     no
        # confirmed    yes      True   n/a
        #               no     False   n/a
        #           ctrl+c     False   n/a
        # So we have to walk through this.
        if not responses:  # ctrl+c from the filename prompt
            return False
        proposed_path = Path(responses["ini"])
        if not proposed_path.exists():  # doesn't exist: confirmation was unnecessary
            build_path = proposed_path
            break
        if "confirmed" not in responses:  # exists but ctrl+c from conf
            return False
        if responses["confirmed"]:
            build_path = responses["ini"]
            break
    return Path(build_path).resolve()


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
    nowish = dt.now().strftime(r"%Y-%m-%d %H:%M:%S")
    intro = [
        f"# laforge configuration generated at",
        f"# {path}",
        f"# {nowish}",
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

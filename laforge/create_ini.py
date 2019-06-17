""" Create a new build INI. """

from pathlib import Path
import time
from collections import namedtuple
from datetime import datetime as dt
from typing import Any, ItemsView, List, Union

from . import toolbox

_CONFIG_TEMPLATE = r"""
[config]
output_dir = {output_dir}'
data_dir = {data_dir}
script_dir = {script_dir}
stata_executable = {stata_executable}

[config.sql]
distro = '{distro}'
server = '{server}'
database = '{database}'
schema = '{schema}'
"""

import click


def create_ini(path: Union[str, Path], debug: bool) -> None:
    path = Path(path)
    if path.suffix not in (".ini",):
        print("WARNING: canonical ending of laforge build file is INI.")

    print("Initializing a new laforge build config file: {}".format(path))
    if path.exists():
        print("\nWARNING -- will overwrite existing file!")
        time.sleep(2)

    responses = get_responses()
    output = create_output(responses)
    toolbox.prepare_to_access(path)
    path.write_text(output)
    print("\nNew laforge build config file written at: {}".format(path))
    exit(0)


ConfigOption = namedtuple("ConfigOption", ["category", "name", "default", "desc"])


def get_responses() -> ItemsView[ConfigOption, Union[None, str, bool]]:
    cumulative_responses = {}
    skipping: List[str] = []

    options = (
        # ConfigOption("dir", "build", ".", "Build directory"),
        ConfigOption(
            "main",
            "data_dir",
            "./data/",
            "Default/relative directory for READ operations. "
            "Can be absolute or relative to the location of the build ini.",
        ),
        ConfigOption(
            "main",
            "output_dir",
            "./output/",
            "Default/relative directory for WRITE operations",
        ),
        ConfigOption(
            "main",
            "script_dir",
            ".",
            "Default/relative directory for EXECUTE (.py, .sql) operations",
        ),
        ConfigOption(
            "main", "shell_dir", ".", "Default/relative directory for SHELL operations"
        ),
        ConfigOption("_fork", "sql", True, "Add SQL configuration?"),
        ConfigOption(
            "sql", "distro", None, "SQL distribution, e.g., MSSQL, MySQL, sqlite)"
        ),
        ConfigOption("sql", "server", None, "SQL server"),
        ConfigOption("sql", "database", None, "SQL database"),
        ConfigOption("sql", "schema", None, "SQL schema"),
    )

    for option in options:
        category, name, default, desc = option
        if category in skipping:
            continue
        response = input(
            "\n{desc}\n> {name} [{default}] ".format(
                name=name, desc=desc, default=default
            )
        ).strip()
        answer = adjudicate(response, default)
        if category == "_fork":
            if not answer:
                skipping.append(name)
        else:
            cumulative_responses[option] = answer
    return cumulative_responses.items()


_VALUE_TO_ENTRY = {True: ("yes", "y", "true", "t"), False: ("false", "f", "no", "n")}
_ENTRY_TO_VALUE = {
    value: key for key in _VALUE_TO_ENTRY for value in _VALUE_TO_ENTRY[key]
}


def adjudicate(response: str, default: Any) -> Any:
    if not response:
        return default
    if default is bool(default):
        return _ENTRY_TO_VALUE.get(response, _ENTRY_TO_VALUE.get(response[0]))
    return response


def create_output(answers: ItemsView[ConfigOption, Any]) -> str:
    output = ["# laforge configuration generated {}".format(dt.now()), "[DEFAULT]"]
    for option, answer in answers:
        _, name, _, desc = option
        comment = "# " if answer is None else ""
        output.append("# {desc}".format(desc=desc))
        output.append(
            "{comment}{name} = {answer}\n".format(
                comment=comment, name=name, answer=answer
            )
        )

    example = ["[hello]", "SHELL = echo 'Hello, world!'", ""]
    output.extend(example)
    return "\n".join(output)

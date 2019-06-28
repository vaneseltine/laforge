"""Builder reads and executes tasks and lists of tasks."""

import configparser
import logging
import runpy
import subprocess
import sys
import textwrap
import time
from collections import namedtuple
from enum import Enum
from pathlib import Path
from pprint import pprint

import click
import dotenv
import pandas as pd

from . import toolbox
from .sql import Channel, Script, Table, execute

logger = logging.getLogger(__name__)
logger.debug(__name__)


def show_env(path=None):
    """Show the calculated generic section environment"""
    if path:
        path = Path(path).resolve(strict=True)
        config_str = path.read_text()
        location = path.parent
    else:
        config_str = ""
        location = Path(".")
    task_list = TaskList(from_string=config_str, location=location)
    pprint(task_list.load_section_config())


def run_build(script_path, *, log, debug=False, dry_run=False):
    """laforge's core build command"""
    path = Path(script_path)
    if path.is_dir():
        path = find_build_config_in_directory(path)

    start_time = time.time()
    global logger  # pylint: disable=global-statement
    logger = get_package_logger(log, debug)

    # THEN set logging -- helps avoid importing pandas at debug level

    logger.info("%s launched.", path)
    if debug:
        click.echo("Debug mode is on.")
    logger.debug("Debug mode is on.")

    task_list = TaskList(path, location=path.parent)
    if dry_run:
        task_list.dry_run()
    else:
        task_list.execute()
        elapsed = seconds_since(start_time)
        logger.info("%s completed in %s seconds.", path, elapsed)


def find_build_config_in_directory(path):
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
    elapsed_raw = time.time() - previous_time
    if round_to:
        return round(elapsed_raw, round_to)
    return elapsed_raw


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


class Verb(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    SHELL = "shell"
    EXIST = "exist"


def get_verb(raw):
    translations = {"exists": "exist"}
    verb = translations[raw] if raw in translations else raw
    return Verb(verb)


def is_verb(raw):
    try:
        _ = get_verb(raw)
    except ValueError:
        return False
    return True


class Target(Enum):
    CSV = ".csv"
    DO = ".do"
    DTA = ".dta"
    HTML = ".html"
    JSON = ".json"
    PICKLE = ".pickle"
    PY = ".py"
    SQL = ".sql"
    XLS = ".xls"
    XLSX = ".xlsx"
    RAWQUERY = "SQL query"
    SQLTABLE = "SQL table"
    # NONE = None
    ANY = "(all)"

    @classmethod
    def parse(cls, verb, raw_content):

        assert verb
        content = str(raw_content).strip()

        if ";" in content or "\n" in content:
            return Target.RAWQUERY

        # print(f"verb {verb} raw_content {raw_content} content {content}")
        content_suffix = Path(content).suffix.strip().lower()
        if not content_suffix:
            return Target.SQLTABLE
        try:
            return Target(content_suffix)
        except ValueError:
            return Target.SQLTABLE


FileCall = namedtuple("FileCall", ["method", "kwargs"])


class TaskConstructionError(RuntimeError):
    pass


class TaskExecutionError(RuntimeError):
    pass


class TaskList:
    """TaskList

    .. todo:: Implement cache_results=False
    """

    _SQL_KEYS = ["distro", "server", "database", "schema"]
    _KNOWN_DIRS = {f"{verb.value}_dir": verb for verb in Verb}

    def __init__(self, from_string, location="."):

        self.parser = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation(), strict=False
        )

        self.parser.read_string(from_string)
        self.location = Path(location).resolve(strict=True)
        self.config = self.load_section_config("DEFAULT")

        self.tasks = list(self.load_tasks())
        logger.debug("Loaded %s tasks.", len(self.tasks))
        self.prior_results = None

    def load_tasks(self):
        skip_to_start = self.parser.has_section("start")
        if skip_to_start:
            logger.warning("Starting execution at section [start].")
        for section in self.parser:
            if skip_to_start:
                if section != "start":
                    continue
                skip_to_start = False
            if section == self.parser.default_section:
                continue
            logger.debug("Loading section %s", section)
            if section.lower() in ("stop", "halt", "quit", "exit"):
                logger.warning(
                    "Will only execute until -- and not including -- "
                    "the section titled [%s].",
                    section,
                )
                break
            section_config = self.load_section_config(section)
            section_config["section"] = section
            # Each section can have up to 1 of each verb as a key
            for option in self.parser[section]:
                if not is_verb(option):
                    continue
                raw_content = self.parser[section][option]
                if raw_content is None:
                    continue
                templated_content = self.template_content(raw_content, section_config)
                task = Task.from_strings(
                    raw_verb=option,
                    raw_content=templated_content,
                    config=section_config,
                )
                logger.debug(task)
                yield task

    @classmethod
    def template_content(cls, content, config):
        new_content = str(content).strip()
        # Passing content through a formatter
        # Allows, e.g., read = {write_dir}/output.csv
        if "{" in new_content or "}" in new_content:
            print(content)
            print("presto change-o")
            formattable_config = {k: v for k, v in config.items() if isinstance(k, str)}
            new_content = new_content.format(**formattable_config)
            print(new_content)
        return new_content

    def load_section_config(self, section="DEFAULT"):
        """Put together config from env, TaskList config, section config"""

        specified_build = Path(self.parser[section].get("build_dir", "."))
        build_dir = self.location / specified_build
        section_config = {}
        section_config["build_dir"] = build_dir.resolve(strict=True)

        dotenv.load_dotenv(build_dir)
        env_config = dotenv.dotenv_values()
        tasklist_config = dict(self.parser["DEFAULT"])
        raw_section_config = dict(self.parser[section])

        from collections import ChainMap

        chained_dicts = ChainMap(raw_section_config, tasklist_config, env_config)
        collapsed_dict = dict(chained_dicts)

        # Load in SQL
        section_config["sql"] = {k: collapsed_dict.get(k) for k in self._SQL_KEYS if k}

        # Load in directories
        section_config["dir"] = {}
        for human, robot in self._KNOWN_DIRS.items():
            section_config["dir"][robot] = build_dir / collapsed_dict.get(human, ".")
            # section_config[human] = section_config["dir"][robot]

        ignorables = self._SQL_KEYS + list(self._KNOWN_DIRS) + list(section_config)

        section_config.update(
            {k: v for k, v in collapsed_dict.items() if k not in ignorables}
        )
        return section_config

    def execute(self):
        """Execute each task in the list.

        .. todo::

            Restore quiet?

        """
        n_tasks = len(self)
        for i, task in enumerate(self.tasks):
            log_prefix = f"Task {i + 1} of {n_tasks}: "
            log_intro = f"{log_prefix}{task.identifier} {task.description}"

            logger.info(log_intro)
            # rotate results during implementation
            self.prior_results = task.implement(self.prior_results)
            logger.debug("%s complete", log_prefix)

    def dry_run(self):
        """List each task in the list. """
        for i, task in enumerate(self.tasks):
            logger.info(f"{(i + 1):>2}/{len(self)}: {str(task)}")

    def __len__(self):
        return len(self.tasks)

    def __repr__(self):
        return "<{} - {} - ({} tasks)>".format(
            self.__class__.__name__, self.location, len(self)
        )


class Task:

    _universal_handlers = {}
    _handlers = {}

    @classmethod
    def from_strings(cls, *, raw_verb, raw_content, config=None):
        if not config:
            config = {}
        identifier = f"{config.get('section', '')}.{raw_verb}"

        verb = get_verb(raw_verb)

        if verb in cls._universal_handlers:
            target = Target.ANY  # No need to try to parse content.
        else:
            # target = cls.determine_target(verb, raw_content)
            target = Target.parse(verb, raw_content)

        handler = cls._get_handler(verb, target)
        return handler(
            identifier=identifier,
            verb=verb,
            target=target,
            content=raw_content,
            config=config,
        )

    @classmethod
    def from_qualified(cls, verb, target, content, config=None, identifier=None):
        handler = cls._get_handler(verb, target)
        if not identifier:
            identifier = "TBD"
        return handler(
            identifier=identifier,
            verb=verb,
            target=target,
            content=content,
            config=config,
        )

    @classmethod
    def _get_handler(cls, verb, target):
        try:
            handler = cls._universal_handlers.get(verb) or cls._handlers[(verb, target)]
        except KeyError:
            raise TaskConstructionError(
                "No handler for verb <{}>, target <{}>".format(verb, target)
            )
        return handler

    @classmethod
    def register(cls, verb, target=Target.ANY):
        def decorator(delegate):
            if target is Target.ANY:
                cls._universal_handlers[verb] = delegate
                # cls._handlers[verb] = delegate
            else:
                cls._handlers[(verb, target)] = delegate
            return delegate

        return decorator

    def implement(self, prior_results=None):
        """Must be implemented by registered classe(s)"""
        raise NotImplementedError

    @property
    def identifier(self):
        """Must be implemented by registered classe(s)"""
        raise NotImplementedError

    @property
    def description(self):
        """Must be implemented by registered classe(s)"""
        raise NotImplementedError


class BaseTask:
    """Create a task to (verb) (something)

    .. todo::

            if ":" in self.content:
               previous_result_key, actual_path_content = self.content.split(":")

    """

    def __init__(self, *, identifier, verb, target, content, config):
        """
        Initialize Task.
        """
        self.identifier = identifier
        self.verb = verb
        self.target = target
        self.content = content
        self.config = config
        self.description = config.get("description", "")

    def implement(self, prior_results=None):
        raise NotImplementedError

    @property
    def path(self):
        """For handlers where dir[verb] + content = path"""
        print(self.config)
        parent = Path(self.config["dir"].get(self.verb, "."))
        return parent / self.content

    def validate_results(self, results):
        if results is None:
            raise TaskExecutionError(
                "No prior results available for {} to write to {}".format(
                    self.__class__.__name__, self.path
                )
            )

    @property
    def short_content(self):
        if " " not in self.content:
            return self.content
        return textwrap.shorten(repr(self.content), 80)

    def __str__(self):
        # return repr(self) + "hi"
        return f"{self.identifier:<30} {self.target.name:<10} {self.content}"

    def __repr__(self):
        return "<{}({}, {}, '{}')>".format(
            self.__class__.__name__, self.verb, self.target, self.short_content
        )


@Task.register(Verb.READ, Target.CSV)
@Task.register(Verb.READ, Target.DTA)
@Task.register(Verb.READ, Target.XLS)
@Task.register(Verb.READ, Target.XLSX)
class FileReader(BaseTask):

    filetypes = {
        Target.CSV: FileCall(
            method="read_csv", kwargs={"keep_default_na": False, "na_values": [""]}
        ),
        Target.DTA: FileCall(method="read_stata", kwargs={}),
        Target.XLS: FileCall(method="read_excel", kwargs={"dtype"}),
        Target.XLSX: FileCall(method="read_excel", kwargs={"dtype"}),
    }

    def implement(self, prior_results=None):
        logger.debug("Reading %s", self.path)
        method, kwargs = self.filetypes[self.target]
        print(self.path)
        df = getattr(pd, method)(self.path, **kwargs)
        logger.info("Read %s", self.path)
        return df


@Task.register(Verb.EXECUTE, Target.PY)
class InternalPythonExecutor(BaseTask):
    """Execute (without importing) Python script by path

    This will set `__main__ = 'laforge'`

    ..todo ::

        Allow implict/explicit return of results.

    """

    def implement(self, prior_results=None):

        logger.debug("Running %s", self.path)
        runpy.run_path(
            str(self.path),
            init_globals={"config": self.config, "prior_results": prior_results},
            run_name="laforge",
        )
        logger.info("Executed: %s", self.path)


@Task.register(Verb.SHELL)
class ShellExecutor(BaseTask):
    def implement(self, prior_results=None):
        logger.debug("Executing: %s", self.content)
        run_cmd(
            full_command=self.content.split(" "),
            cwd=self.config["dir"][Verb.SHELL],
            shell=True,
        )
        logger.info("Executed: %s", self.content)


def run_cmd(full_command, cwd=None, shell=False):
    return subprocess.run(full_command, cwd=cwd, shell=shell, check=True)


@Task.register(Verb.EXECUTE, Target.DO)
class StataExecutor(BaseTask):
    def implement(self, prior_results=None):
        stata_exe = Path(self.config["stata_executable"])
        assert stata_exe.exists()
        do_parameters = self.config.get("stata_parameters", [])
        do_path = self.path.absolute()
        logger.info("Executing %s", do_path)
        stata_command_list = [stata_exe, "/e", "do", do_path] + do_parameters
        full_command = [str(x) for x in stata_command_list]

        run_cmd(full_command=full_command, cwd=do_path.parent, shell=False)
        logger.info("Executed: %s", do_path)


@Task.register(Verb.READ, Target.RAWQUERY)
@Task.register(Verb.EXECUTE, Target.RAWQUERY)
class SQLQueryReader(BaseTask):
    def implement(self, prior_results=None):
        logger.debug("Reading from %s", self.short_content)
        fetch = "df"
        if self.verb is Verb.EXECUTE:
            fetch = False
        df = execute(self.content, channel=Channel(**self.config["sql"]), fetch=fetch)
        logger.info("Read in from %s", self.short_content)
        return df


@Task.register(Verb.EXECUTE, Target.SQL)
class SQLExecutor(BaseTask):
    def implement(self, prior_results=None):
        query = self.path.read_text()
        query_len = query.count("\n")
        logger.debug(f"Query for execution is {query_len} lines long.")
        sql_script = Script(query, channel=Channel(**self.config["sql"]))
        sql_script.execute()
        logger.debug("Executed: %s", self.content)


@Task.register(Verb.READ, Target.SQLTABLE)
@Task.register(Verb.WRITE, Target.SQLTABLE)
class SQLReaderWriter(BaseTask):
    def implement(self, prior_results=None):
        table = Table(self.content, channel=Channel(**self.config["sql"]))
        if self.verb is Verb.WRITE:
            logger.debug("Writing %s", table)
            self.validate_results(prior_results)
            table.write(prior_results)
            logger.info("Wrote %s", table)
            return None

        logger.debug("Reading %s", table)
        df = table.read()
        logger.info("Read %s", table)
        return df


@Task.register(Verb.WRITE, Target.CSV)
@Task.register(Verb.WRITE, Target.DTA)
@Task.register(Verb.WRITE, Target.HTML)
@Task.register(Verb.WRITE, Target.XLSX)
class FileWriter(BaseTask):
    """Handles all tasks writing to file."""

    filetypes = {
        Target.CSV: FileCall(method="to_csv", kwargs={"index": False}),
        Target.DTA: FileCall(method="to_stata", kwargs={"write_index": False}),
        Target.HTML: FileCall(
            method="to_html",
            kwargs={"show_dimensions": True, "justify": "left", "index": False},
        ),
        Target.XLSX: FileCall(method="to_excel", kwargs={"index": False}),
    }

    def implement(self, prior_results=None):
        logger.debug("Writing %s", self.path)
        self.validate_results(prior_results)
        self.write(path=self.path, target=self.target, df=prior_results)
        logger.info("Wrote %s", self.path)

    @classmethod
    def write(cls, *, path, target, df):
        logger.debug(
            f"Preparing to write {len(df):,} rows, {len(df.columns)} columns to {path}"
        )
        # Weirdly, this affects html output as well
        pd.set_option("display.max_colwidth", 100)

        if df.empty:
            logger.warning(f"Writing an empty dataset to {path}")
        toolbox.prepare_to_access(path)
        method, kwargs = cls.filetypes[target]
        getattr(df, method)(path, **kwargs)


@Task.register(Verb.EXIST)
class ExistenceChecker(BaseTask):
    def implement(self, prior_results=None):
        # Ensure that some content exists in these lines
        lines = [s for s in self.content.splitlines() if s.strip()]
        assert lines, "Accidental blank line?"
        for line in lines:
            target = Target.parse(self.verb, line)
            logger.debug(f"Verifying that {line} ({target}) exists...")
            if target is Target.SQLTABLE:
                self._check_existence_sql_table(line)
            elif target is Target.RAWQUERY:
                self._check_existence_sql_raw_query(line)
            else:
                self._check_existence_path(line)
            logger.info(f"Verified that {line} exists.")

    def _check_existence_path(self, line):
        path = self.config["dir"][Verb.EXIST] / line
        if not path.exists():
            raise FileNotFoundError(path)

    def _check_existence_sql_table(self, line):
        table = Table(line, channel=Channel(**self.config["sql"]))
        assert table.exists()

    def _check_existence_sql_raw_query(self, line):
        df = execute(line, channel=Channel(**self.config["sql"]), fetch="df")
        assert not df.empty


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

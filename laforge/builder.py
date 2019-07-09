"""Builder reads and executes tasks and lists of tasks."""

import configparser
import logging
import os
import runpy
import subprocess
import textwrap
import time
from collections import namedtuple
from enum import Enum
from pathlib import Path

import dotenv
import pandas as pd

from .sql import Channel, Script, Table, execute

logger = logging.getLogger(__name__)
logger.debug(__name__)


def show_env(path):
    """Show the calculated generic section environment"""
    from_string = path.read_text() if path.is_file() else ""
    location = path.parent if path.is_file() else path
    task_list = TaskList(from_string=from_string, location=location)
    return task_list.load_section_config()


class Verb(Enum):
    READ = "read"
    WRITE = "write"
    ECHO = "echo"
    EXECUTE = "execute"
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
    ANY = "(all)"

    @classmethod
    def parse(cls, verb, raw_content):

        assert verb
        content = str(raw_content).strip()

        if ";" in content or "\n" in content:
            return Target.RAWQUERY

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

        self.env_config = load_env(self.location)

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
            formattable_config = {k: v for k, v in config.items() if isinstance(k, str)}
            new_content = new_content.format(**formattable_config)
        return new_content

    def load_section_config(self, section="DEFAULT"):
        """Put together config from env, TaskList config, section config"""

        specified_build = Path(self.parser[section].get("build_dir", "."))
        build_dir = self.location / specified_build
        section_config = {}
        section_config["build_dir"] = build_dir.resolve(strict=True)

        tasklist_config = dict(self.parser["DEFAULT"])
        raw_section_config = dict(self.parser[section])

        from collections import ChainMap

        chained_dicts = ChainMap(raw_section_config, tasklist_config, self.env_config)
        collapsed_dict = dict(chained_dicts)

        # Load in SQL
        section_config["sql"] = {k: collapsed_dict.get(k) for k in self._SQL_KEYS if k}

        # Load in directories
        section_config["dir"] = {}
        for human, robot in self._KNOWN_DIRS.items():
            section_config["dir"][robot] = build_dir / collapsed_dict.get(human, ".")

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
            # Rotate results during implementation
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
    def from_strings(cls, *, raw_verb, raw_content, config):
        verb = get_verb(raw_verb)
        if verb in cls._handlers:
            target = Target.ANY
        else:
            target = Target.parse(verb, raw_content)
        return cls.from_qualified(
            verb=verb,
            target=target,
            content=raw_content,
            config=config,
            identifier=f"{config.get('section', '')}.{raw_verb}",
        )

    @classmethod
    def from_qualified(cls, verb, target, content, config=None, identifier="TBD"):
        handler = cls._get_handler(verb, target)
        return handler(
            identifier=identifier,
            verb=verb,
            target=target,
            content=content,
            config=config,
        )

    @classmethod
    def _get_handler(cls, verb, target):
        handler = cls._handlers.get(verb, None)
        if handler:
            return handler
        handler = cls._handlers.get((verb, target), None)
        if handler:
            return handler
        raise TaskConstructionError(f"No handler for verb <{verb}>, target <{target}>")

    @classmethod
    def register(cls, verb, target=Target.ANY):
        def decorator(delegate):
            if target is Target.ANY:
                cls._handlers[verb] = delegate
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
        Target.XLS: FileCall(method="read_excel", kwargs={}),  # kwargs={"dtype"}),
        Target.XLSX: FileCall(method="read_excel", kwargs={}),  # kwargs={"dtype"}),
    }

    def implement(self, prior_results=None):
        logger.debug("Reading %s", self.path)
        method, kwargs = self.filetypes[self.target]
        df = getattr(pd, method)(self.path, **kwargs)
        logger.info("Read %s", self.path)
        return df


@Task.register(Verb.EXECUTE, Target.PY)
class InternalPythonExecutor(BaseTask):
    """Execute (without importing) Python script by path

    Allows script adjustment via setting the run name: `__main__ = 'laforge'`

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


@Task.register(Verb.ECHO)
class Echoer(BaseTask):
    def implement(self, prior_results=None):
        logger.debug(f"Echoing {self.content}")
        print(self.content)


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
        subprocess.run(
            full_command=full_command, cwd=do_path.parent, shell=False, check=True
        )
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
@Task.register(Verb.WRITE, Target.XLS)
class FileWriter(BaseTask):
    """Handles all tasks writing to file."""

    filetypes = {
        Target.CSV: FileCall(method="to_csv", kwargs={"index": False}),
        Target.DTA: FileCall(method="to_stata", kwargs={"write_index": False}),
        Target.HTML: FileCall(
            method="to_html",
            kwargs={"show_dimensions": True, "justify": "left", "index": False},
        ),
        Target.XLSX: FileCall(
            method="to_excel", kwargs={"index": False, "engine": "xlsxwriter"}
        ),
        Target.XLS: FileCall(
            method="to_excel", kwargs={"index": False, "engine": "xlsxwriter"}
        ),
    }

    def implement(self, prior_results=None):
        logger.debug("Writing %s", self.path)
        self.validate_results(prior_results)
        self.write(path=self.path, target=self.target, df=prior_results)
        logger.info("Wrote %s", self.path)

    @classmethod
    def write(cls, *, path, target, df, retry_attempts=3, retry_seconds=5):
        logger.debug(
            f"Preparing to write {len(df):,} rows, {len(df.columns)} columns to {path}"
        )

        pd.set_option("display.max_colwidth", 100)  # Weirdly affects html output

        if df.empty:
            logger.warning(f"Writing an empty dataset to {path}")
        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        method, kwargs = cls.filetypes[target]

        for i in range(retry_attempts):
            try:
                getattr(df, method)(path, **kwargs)
                return None
            except PermissionError:
                error_message = (
                    f"Permission denied to {path}. Is it open in another program?"
                )
                logger.error(error_message)
            remaining = retry_attempts - i
            logger.error(
                "%s attempt(s) remaining. Trying %s again in %s second(s)...",
                remaining,
                path,
                retry_seconds,
            )
            time.sleep(retry_seconds)
        raise PermissionError(f"Permission denied to {path}")


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


class DirectoryVisit:
    def __init__(self, path):
        self.old = Path(".").resolve()
        self.new = Path(path).resolve()
        if self.old != self.new:
            os.chdir(self.new)

    def __enter__(self):
        return self.new

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        if self.old != self.new:
            os.chdir(self.old)


def load_env(path):
    """Get .env values without dotenv's default to silently pull package dir"""
    with DirectoryVisit(path):
        try:
            env_config = dotenv.dotenv_values(
                dotenv.find_dotenv(usecwd=True, raise_error_if_not_found=True)
            )
        except IOError:
            env_config = {}
    return env_config


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

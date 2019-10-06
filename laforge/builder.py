"""Builder reads and executes tasks."""

import logging
import os
import textwrap
import time
from collections import namedtuple
from enum import Enum
from pathlib import Path

import dotenv
import pandas as pd

from .sql import Channel, Script, Table, execute

logger = logging.getLogger(__name__)
logger.debug(logger.name)


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
    def parse(cls, raw_content):

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


class Task:

    _universal_handlers = {}
    _handlers = {}

    @classmethod
    def from_strings(cls, *, raw_verb, raw_content, config):
        verb = get_verb(raw_verb)
        if verb in cls._handlers:
            target = Target.ANY
        else:
            target = Target.parse(raw_content)
        return cls.from_qualified(
            home=NotImplemented,
            verb=verb,
            target=target,
            content=raw_content,
            config=config,
        )

    @classmethod
    def from_qualified(cls, home, verb, target, content, config=None):
        handler = cls._get_handler(verb, target)
        from .command import HOME

        return handler(
            home=HOME, verb=verb, target=target, content=content, config=config
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


class BaseTask:
    """Create a task to (verb) (something)"""

    def __init__(self, *, home, verb, target, content, config):
        self.home = home.resolve()
        self.verb = verb
        self.target = target
        self.content = content
        self.config = config

    def implement(self, prior_results=None):
        raise NotImplementedError

    @property
    def path(self):
        """For handlers where dir[verb] + content = path"""
        return (self.home / self.content).resolve()

    def validate_results(self, results):
        if results is None:
            raise TaskExecutionError(
                "No prior results available for {} to write to {}".format(
                    self.__class__.__name__, self.path
                )
            )

    @property
    def short_content(self):
        return textwrap.shorten(repr(self.content), 80)

    def __str__(self):
        return f"{self.__class__.__name__:<30} {self.target.name:<10} {self.content}"

    def __repr__(self):
        return "<{}({}, {}, '{}')>".format(
            self.__class__.__name__, self.verb, self.target, self.short_content
        )


@Task.register(Verb.READ, Target.CSV)
@Task.register(Verb.READ, Target.XLS)
@Task.register(Verb.READ, Target.XLSX)
class FileReader(BaseTask):

    filetypes = {
        Target.CSV: FileCall(
            method="read_csv", kwargs={"keep_default_na": False, "na_values": [""]}
        ),
        Target.XLS: FileCall(method="read_excel", kwargs={}),  # kwargs={"dtype"}),
        Target.XLSX: FileCall(method="read_excel", kwargs={}),  # kwargs={"dtype"}),
    }

    def implement(self, prior_results=None):
        logger.debug("Reading %s", self.path)
        method, kwargs = self.filetypes[self.target]
        df = getattr(pd, method)(self.path, **kwargs)
        logger.info("Read %s", self.path)
        return df


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
@Task.register(Verb.WRITE, Target.HTML)
@Task.register(Verb.WRITE, Target.XLSX)
@Task.register(Verb.WRITE, Target.XLS)
class FileWriter(BaseTask):
    """Handles all tasks writing to file."""

    filetypes = {
        Target.CSV: FileCall(method="to_csv", kwargs={"index": False}),
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
            target = Target.parse(line)
            logger.debug(f"Verifying that {line} ({target}) exists...")
            if target is Target.SQLTABLE:
                self._check_existence_sql_table(line)
            elif target is Target.RAWQUERY:
                self._check_existence_sql_raw_query(line)
            else:
                self._check_existence_path(line)
            logger.info(f"Verified that {line} exists.")

    def _check_existence_path(self, line):
        path = self.build_dir / line
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

""".garnish provides decorators for common data tasks."""

import functools
import logging
import textwrap
import time
from collections import namedtuple
from enum import Enum
from pathlib import Path

import pandas as pd

from . import sql

logger = logging.getLogger(__name__)
logger.debug(logger.name)

RESULTS = {}


class Verb(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    EXIST = "exist"


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
    def from_qualified(cls, verb, target, content, config=None):
        handler = cls._get_handler(verb, target)
        return handler(verb=verb, target=target, content=content, config=config)

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

    home = Path(".")

    def __init__(self, *, verb, target, content, config=None):
        self.verb = verb
        self.target = target
        self.content = content
        self.config = config or {}
        print("x" * 50, repr(self.config))

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
        channel = sql.Channel(**self.config["sql"]) if "sql" in self.config else None
        script = sql.Script(self.content, channel=channel)

        result = None
        if self.verb is Verb.EXECUTE:
            script.execute()
        else:
            result = script.to_table()

        logger.info("Read in from %s", self.short_content)
        return result


@Task.register(Verb.READ, Target.SQLTABLE)
@Task.register(Verb.WRITE, Target.SQLTABLE)
class SQLReaderWriter(BaseTask):
    def implement(self, prior_results=None):

        if "sql" in self.config:
            channel = sql.Channel(**self.config["sql"])
        else:
            channel = None
        table = sql.Table(self.content, channel=channel)
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

        pd.set_option("display.max_colwidth", 100)  # Weirdly, affects html output

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
        target = Target.parse(self.content)
        logger.debug(f"Verifying that {self.content} ({target}) exists...")
        if target is Target.SQLTABLE:
            self._check_existence_sql_table(self.content)
        elif target is Target.RAWQUERY:
            self._check_existence_sql_raw_query(self.content)
        else:
            self._check_existence_path(self.content)
        logger.info(f"Verified that {self.content} exists.")

    def _check_existence_path(self, line):
        path = self.home / line
        if not path.exists():
            raise FileNotFoundError(path)

    def _check_existence_sql_table(self, line):

        if "sql" in self.config:
            channel = sql.Channel(**self.config["sql"])
        else:
            channel = None

        table = sql.Table(line, channel=channel)
        assert table.exists()

    def _check_existence_sql_raw_query(self, line):
        df = sql.execute(line, channel=sql.Channel(**self.config["sql"]), fetch="df")
        assert not df.empty


def save(variable):
    """Save return value of decorated function under `variable`."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            result = func(*args, **kwargs)
            RESULTS[variable] = result
            logger.debug(f"Saved a {type(result)} under RESULTS['{variable}']...")
            return result

        return wrapper_func

    return decorator_func


def write(content):
    """Return value will be written to specified target."""
    logger.debug(f"Writing a return value to {content}.")

    def decorator_write(func):
        @functools.wraps(func)
        def wrapped_write(*args, **kwargs):
            result = func(*args, **kwargs)
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.WRITE, target=target, content=content)
            task.implement(result)
            return result

        return wrapped_write

    return decorator_write


def load(variable):
    """Retrieve earlier result previously saved under `variable`."""

    def decorator_func(func):
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            # Invoke the wrapped function first
            kwargs[variable] = RESULTS[variable]
            logger.debug(
                f"Retrieved a {type(kwargs[variable])} under RESULTS['{variable}']..."
            )
            result = func(*args, **kwargs)
            return result

        return wrapper_func

    return decorator_func


def read(variable, content):
    """Pass DataFrame of target into function parameters"""
    logger.debug(f"Adding a read of {content}, passing in as {variable}")

    def decorator_read(func):
        @functools.wraps(func)
        def wrapped_read(*args, **kwargs):
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.READ, target=target, content=content)
            result = task.implement()
            kwargs[variable] = result
            return functools.partial(func, *args, **kwargs)()

        return wrapped_read

    return decorator_read


def exists(content):
    """Pass DataFrame of target into function parameters"""
    logger.debug(f"Adding a existence check on {content}")

    def decorator_exists(func):
        @functools.wraps(func)
        def wrapped_exists(*args, **kwargs):
            target = Target.parse(content)
            task = Task.from_qualified(verb=Verb.EXIST, target=target, content=content)
            try:
                task.implement()
            except FileNotFoundError:
                exit_failure(f"Could not verify existence of {content}", task)
            return func(*args, **kwargs)

        return wrapped_exists

    return decorator_exists


def exit_failure(reason, task):
    logger.error(reason)
    logger.debug(repr(task))
    exit(9)

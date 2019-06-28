#!/usr/bin/env python3
"""SQL utilities for mid-level interaction. Inspired by pathlib; powered by SQLALchemy.

.. note::

    Supported: MSSQL, MariaDB/MySQL, PostgreSQL, SQLite.
    Supportable: Firebird, Oracle, Sybase.

"""

import logging
import re
import textwrap

import pandas as pd
import pyparsing
import sqlalchemy as sa

from . import toolbox

logger = logging.getLogger(__name__)
logger.debug(__name__)


class SQLTableNotFound(Exception):
    pass


class SQLChannelNotFound(Exception):
    pass


class SQLIdentifierProblem(ValueError):
    pass


class Channel:
    """Abstraction from Engine, other static details."""

    known_engines = {}
    known_channels = {}

    def __init__(
        self, distro, *, server=None, database=None, schema=None, **engine_kwargs
    ):
        from .distros import Distro

        self.distro = Distro.get(distro)
        self.server = server
        self.database = database
        self.schema = schema

        self.engine = self._construct_engine(**engine_kwargs)
        self.save_engine()
        self.metadata = sa.MetaData(bind=self.engine, schema=self.schema)

        if self.metadata.bind.url.database:
            self.database = self.metadata.bind.url.database

        try:
            self.inspector = sa.inspect(self.engine)
        except sa.exc.DBAPIError:
            logger.warning("Ignoring pretend table.")

    @classmethod
    def grab(cls):
        if not cls.known_channels:
            raise SQLChannelNotFound("No known SQL channels exist.")
        if len(cls.known_channels) == 1:
            return next(iter(cls.known_channels.values()))
        raise SQLChannelNotFound("Cannot select from more than one SQL channel.")

    def _construct_engine(self, **engine_kwargs):
        existing_engine = self.retrieve_engine()
        if existing_engine:
            return existing_engine
        return self.distro.create_engine(
            server=self.server, database=self.database, engine_kwargs=engine_kwargs
        )

    def retrieve_engine(self):
        return self._retrieve_engine(repr(self))

    @classmethod
    def _retrieve_engine(cls, key):
        return cls.known_engines.get(key)

    def save_engine(self):
        self._save_engine(self, repr(self), self.engine)

    @classmethod
    def _save_engine(cls, channel, key, engine):
        if key not in cls.known_engines:
            cls.known_engines[key] = engine
        if engine not in cls.known_channels:
            cls.known_channels[engine] = channel

    def execute_statement(self, statement, fetch=False):
        """Execute SQL (core method)

        .. todo::

            De-messify

        """
        statement = self.clean_up_statement(statement)
        assert fetch in ("df", "tuples", False)
        if fetch == "df":
            try:
                return pd.read_sql(statement, con=self.engine)
            except Exception as err:
                logger.error(
                    "Error reading SQL to DF using %s\nExecuting:\n\n%s\n\n",
                    self.engine,
                    statement,
                )
                raise err
        final_result = None
        with self.engine.connect() as cnxn:
            with cnxn.begin() as transxn:
                try:
                    result = cnxn.execution_options(autocommit=True).execute(statement)
                    if fetch == "tuples":
                        final_result = result.fetchall()
                finally:
                    transxn.commit()
        return final_result

    @staticmethod
    def clean_up_statement(s):
        s = s.strip()
        for quote_char in ('"', "'"):
            while s.startswith(quote_char) and s.endswith(quote_char):
                s = s.strip(quote_char)
        return s

    def find(self, object_pattern="%", schema_pattern="%"):
        return self.distro.find(
            channel=self, object_pattern=object_pattern, schema_pattern=schema_pattern
        )

    def __hash__(self):
        return hash(
            str(x) for x in (self.distro, self.server, self.database, self.schema) if x
        )

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        pieces = ";".join(
            str(x) for x in (self.distro, self.server, self.database, self.schema) if x
        )
        return f"{self.__class__.__name__}({pieces})"


def execute(statement, fetch=False, channel=None):
    """Convenience method, autofetches Channel if possible"""
    if not channel:
        channel = Channel.grab()
    return channel.execute_statement(statement, fetch=fetch)


class Script:
    """SQL query string, parsable by 'go' separation and execute()able."""

    BATCH_TERMINATOR = "go"
    _batch_borders = re.compile(r"\n[^\w;\d-]*go\W*?\n", flags=re.IGNORECASE)
    _terminating_batch_terminator = re.compile(r"(?<=\W)(go\W*)+$", flags=re.IGNORECASE)
    _terminating_semicolon = re.compile(r"[\s;]+$")

    def __init__(self, query, channel=None):
        if not channel:
            channel = Channel.grab()
        self.channel = channel
        self.query = query
        self._query_string = self._remove_comments(query)
        self.parsed = self._parse(self._query_string)

    @classmethod
    def _remove_comments(cls, input_string):
        lines = cls._remove_multiline_sql_comment(input_string).splitlines()
        new_lines = (cls._remove_double_dash_sql_comment(l) for l in lines)
        return "\n".join(new_lines)

    def _parse(self, query):
        flattened_group = toolbox.flatten(self._construct_statements(query))
        return [s for s in flattened_group if self._is_useful_statement(s)]

    def _construct_statements(self, query):
        return [
            self._normalize_batch_end(batch)
            for batch in self._break_into_batches(query)
        ]

    def _break_into_batches(self, query):
        """.. todo::

            Parse multiple go in a row more elegantly, avoid injecting line breaks.
            Cf. _format_statement

        """
        batches = self._batch_borders.split(query)
        return [batch.strip() for batch in batches]

    @classmethod
    def _normalize_batch_end(cls, batch):
        batch = batch.strip()
        batch = cls._terminating_semicolon.sub("", batch)
        batch = cls._terminating_batch_terminator.sub(r"", batch)
        batch = cls._terminating_semicolon.sub("", batch)
        return batch + ";"

    @staticmethod
    def _is_useful_statement(s):
        return re.findall("[A-Za-z]", s)

    @staticmethod
    def _remove_multiline_sql_comment(input_string):
        cleansed = (
            pyparsing.nestedExpr("/*", "*/").suppress().transformString(input_string)
        )
        return cleansed

    @staticmethod
    def _remove_double_dash_sql_comment(single_line):
        double_dash_pattern = re.compile(r"\s*?--.*")
        return double_dash_pattern.sub("", single_line)

    # Public API

    def execute(self, statements=None):
        """Execute itsel(f|ves)"""

        statements = statements or self.parsed
        for i, statement in enumerate(statements):
            logger.debug(
                "Executing statement %s of %s, %s lines long: %s",
                i + 1,
                len(statements),
                statement.count("\n") + 1,
                textwrap.shorten(statement, 80),
            )
            self.channel.execute_statement(statement)

    def to_table(self):
        """Executes all and tries to return a DataFrame for the result of the final query.

        This is one of two ways that laforge retrieves tables.

        .. warning::

            This is limited by the capacity of Pandas to retrieve only the final result.
            For Microsoft SQL Server, if a lengthy set of queries is desired, the most
            reliable approach appears to be a single final query after a 'go' as a batch
            gterminator.

        .. warning::

            This will rename columns that do not conform to naming standards.

        """
        assert isinstance(self.query, str)
        logger.debug("Executing SQL: %s", textwrap.shorten(self.query, 80))
        logger.debug(
            "%s queries prior to retrieval; final for df is %s chars long.",
            len(self.parsed[:-1]),
            len(self.parsed[-1]),
        )
        for stmt in self.parsed[:-1]:
            self.channel.execute_statement(stmt, fetch=False)
        df = self.channel.execute_statement(self.parsed[-1], fetch="df")
        rows, cols = df.shape
        logger.debug("Received %s rows, %s columns.", rows, cols)

        df = fix_bad_columns(df)
        return df

    def read(self):
        return self.to_table()

    def __len__(self):
        return len(self.parsed)

    def __str__(self):
        return "Script: " + "\n".join(q for q in self.parsed)

    def __repr__(self):
        return "<{} of {} statement{}>".format(
            self.__class__.__name__, len(self), ["s", ""][len(self) == 1]
        )


class Table:
    """Represents a SQL table, featuring methods to read/write DataFrames.

    .. todo :: Factor out to superclass to allow views

    """

    def __init__(self, name, channel=None, **kwargs):
        self.channel = channel if channel else Channel.grab()
        self.metadata = self.channel.metadata
        self.distro = self.channel.distro

        identifiers = self._parse_args(name, kwargs)
        for keyword in self.distro.minimal_keywords:
            if not identifiers.get(keyword):
                raise SQLIdentifierProblem(
                    f"Valid {keyword} required from %s", identifiers
                )
        self.__server = self.channel.server
        self.__database = identifiers.get("database", self.channel.database)
        self.__schema = identifiers.get("schema", self.channel.schema)
        try:
            self.__name = identifiers["name"]
        except KeyError:
            raise SQLIdentifierProblem("Must provide table name.")
        self.__metal = None

    @property
    def metal(self):
        if self.__metal is None:
            self.__metal = sa.Table(
                self.name,
                self.metadata,
                autoload=True,
                autoload_with=self.channel.engine,
                extend_existing=True,
            )
        return self.__metal

    @property
    def identifiers(self):
        return {
            "server": self.__server,
            "database": self.__database,
            "schema": self.__schema,
            "name": self.__name,
        }

    @property
    def server(self):
        return self.__server

    @property
    def database(self):
        return self.__database

    @property
    def schema(self):
        return self.__schema

    @property
    def name(self):
        return self.__name

    def _parse_args(self, name, kwargs):

        id_dict = {
            "schema": kwargs.get("schema", self.channel.schema),
            "database": kwargs.get("database", self.channel.database),
            "server": kwargs.get("server", self.channel.server),
        }

        parts_dict = {
            k: v
            for k, v in zip(
                ["name", "schema", "database", "server"], reversed(name.split("."))
            )
            if v
        }
        id_dict.update(parts_dict)
        for key in id_dict:
            if not key or key in self.distro.untouchable_identifiers:
                continue
            id_dict[key] = self._remove_irrelevant_details(id_dict[key])
            Identifier(id_dict[key]).check()
        return id_dict

    @staticmethod
    def _remove_irrelevant_details(raw):
        if not raw:
            return raw
        s = str(raw)
        if s.startswith("[") and s.endswith("]"):
            return s.lstrip("[").rstrip("]")
        return s

    # API

    def exists(self):
        insp = sa.inspect(self.channel.engine)
        tables = insp.get_table_names(schema=self.schema or None)
        return self.name in tables

    def resolve(self, strict=False):
        if strict and not self.exists():
            raise SQLTableNotFound("{} does not exist.".format(self))
        return self.distro.resolver.format(**self.identifiers)

    def write(self, df, if_exists="replace"):
        """From DataFrame, create a new table and fill it with values"""
        if df.empty:
            raise RuntimeError("DataFrame to write is empty!")
        if not isinstance(df, pd.DataFrame):
            raise RuntimeError(f"Can only write DataFrame, not {type(df)}")
        if "" in df.columns:
            df = fix_bad_columns(df)
        dtypes = self.distro.determine_dtypes(df)

        df.to_sql(
            name=self.name,
            con=self.channel.engine,
            schema=self.schema or None,  # sqlite can't use "" or it craps out
            if_exists=if_exists,
            index=False,
            dtype=dtypes,
        )

    def read(self):
        """Return the full table as a DataFrame"""
        select_all = sa.select([self.metal])
        return pd.read_sql(select_all, con=self.metadata.bind)

    def drop(self, ignore_existence=False):
        """Delete the table within SQL"""

        if self.exists():
            self.metal.drop()
        elif not ignore_existence:
            raise SQLTableNotFound(self)
        assert not self.exists()
        logger.debug("%s dropped.", self)

    @property
    def columns(self):
        return self.metal.columns

    def __len__(self):
        count_query = sa.select([sa.func.count()]).select_from(self.metal)
        return int(Scalar(self.metadata.bind.execute(count_query)))

    def __str__(self):
        return self.resolve(strict=False)

    def __repr__(self):
        return f"Table('{self}')"

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.metal)


class Scalar:
    """Little helper to produce clearly typed single (upper left) ResultProxy result."""

    def __init__(self, prox):
        self.item = prox.first()[0]
        prox.close()

    def __int__(self):
        return int(self.item)

    def __str__(self):
        return str(self.item)


class Identifier:
    """Single standardized variable/database/schema/table/column/anything identifier.

    .. todo::
        class InvalidIdentifierError
        relay_id_problem(identifier, action, reason=None, replacement=None)

    """

    # A-Z, a-z, 0-9, @ # $ _ mostly okay for table name following first letter
    VALID_CHARACTERS_AFTER_FIRST = r"[\w@_#$]+"
    # Unless it's the first character, which can't be a number or $
    # So a complete name needs to be a block starting with a proper lead character
    # and (possibly) continuing with valid characters
    VALID_NAME_PATTERN = r"[A-Za-z@_#][\w@_#$]*"

    WHITELIST = [":memory:", "tables"]
    BLACKLIST = ["?column?", ""]

    def __init__(self, user_input, extra=None):
        """

        :param user_input: Something that can be converted into a useful string.

        :param extra: Additional something that could be usefully appended/exchanged
        with the native identifier.

        .. todo:: Can this be fully idempotent?

        .. todo:: Re-validate fallbacks?

        """
        self.original = user_input
        self.extra = extra

        stringed_input = str(self.original)
        try:
            self._leading_underscore = stringed_input.strip().startswith("_")
        except AttributeError:
            raise SQLIdentifierProblem(
                "String or stringlike object required, not {}.".format(stringed_input)
            )
        if stringed_input in self.WHITELIST:
            self.normalized = stringed_input
        elif str(stringed_input) in self.BLACKLIST:
            self.normalized = self._normalize("")
        else:
            self.normalized = self._normalize(stringed_input)

    def check(self):
        if self.normalized != self.original:
            logger.debug(
                "Identifier [%s] suggested normalization: [%s].",
                self.original,
                self.normalized,
            )

    def _normalize(self, working):
        working = self._replace_characters(working)
        working = self._fix(working)
        working = self._stylize(working)
        working = self._shorten(working)
        working = self._amend(working)
        return working

    @classmethod
    def _replace_characters(cls, attempt, replacement="_"):
        # Strip out non-valid characters, replace with replacement
        attempt = replacement.join(
            re.findall(cls.VALID_CHARACTERS_AFTER_FIRST, attempt)
        )
        return attempt

    def _fix(self, s):
        hit = re.search(self.VALID_NAME_PATTERN, s)
        if hit:
            return hit.group(0)
        # Lack of match: no usable first character (could be blank/all specials)
        if self.extra is None:
            raise SQLIdentifierProblem(
                "Could not create a useful name out of empty: {}".format(s)
            )
        fixed = self._force_fix(s, self.extra)
        logger.warning(
            "Could not parse a useful name from: [%s], replaced with: [%s]", s, fixed
        )
        return fixed

    @staticmethod
    def _force_fix(name, extra):
        if not name:
            return "column_{}".format(extra)
        if not name[0].isalpha():
            return "column_{}".format(name)
        return name

    def _stylize(self, attempt):
        # Don't add a leading underscore if it wasn't there already (junk replacement)
        if not self._leading_underscore:
            attempt = attempt.lstrip("_")
        return attempt

    @staticmethod
    def _shorten(s, max_length=62, warning_length=255):
        """Cut off lengthy identifiers.

        .. note ::

            SQL Server allows 128 (116 for temp); postgre 63,  MySQL 64.
            This currently uses 62 as a lowest common denominator.

        :param attempt:
        :param max_length:  (Default value = 62)
        :param warning_length:  (Default value = 255)

        """
        shortened = s[:max_length]
        if shortened == s:
            return s
        display_wings = (max_length + 6) // 2
        display = f"{s[:display_wings]}[...]{s[-display_wings:]}"
        if len(s) >= warning_length:
            logger.warning("Too long to be a reasonable identifier name: %s", display)
        logger.warning("Truncated [%s] into [%s].", display, shortened)
        return shortened

    @classmethod
    def _amend(cls, s, suffix="_"):
        """

        :param attempt:
        :param suffix:  (Default value = "_")

        """
        initial_attempt = s
        while toolbox.is_reserved_word(s):
            s = s + suffix
            assert len(s) > len(initial_attempt)
        if initial_attempt != s:
            logger.debug("Reserved word '%s' amended to '%s'", initial_attempt, s)
        return s

    def __str__(self):
        return self.normalized


def fix_bad_columns(df):
    badnames = set(Identifier.BLACKLIST).intersection(df.columns)
    leading_numbers = any(x for x in df.columns if x[:1].isdigit())
    if not badnames and not leading_numbers:
        return df
    new_columns = [Identifier(c, extra=i).normalized for i, c in enumerate(df.columns)]
    new_df = df.set_axis(labels=new_columns, axis="columns", inplace=False)
    return new_df


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

import logging
import re

from importlib import import_module
from pathlib import Path
from urllib import parse

import sqlalchemy as sa

from .sql import Script, Table
from .toolbox import round_up

logger = logging.getLogger(__name__)
logger.debug(__name__)


class SQLDistroNotFound(Exception):
    pass


class Distro:
    name = "generic"
    driver = ""

    # Note: sqlite only has a generic Integer
    NUMERIC_RANGES = {
        sa.types.SMALLINT: 2 ** 15 - 101,
        sa.types.INT: 2 ** 31 - 101,
        sa.types.BIGINT: 2 ** 63 - 101,
    }
    NUMERIC_PADDING_FACTOR = 10

    large_number_fallback = None
    minimal_keywords = ["server", "schema", "name"]
    untouchable_identifiers = []
    varchar_fallback = None
    varchar_max_specs = -1
    varchar_override = None

    templates = {
        "find": """--Distro.find()
            select table_schema, table_name
            from information_schema.tables
            where table_schema like '{schema_pattern}'
                and table_name like '{object_pattern}';
            """
    }

    _registered_distros = []

    def __init__(self):
        import_module(self.driver)
        self.dialect = import_module(f"sqlalchemy.dialects.{self.name}")

    def determine_dtypes(self, df):
        new_dtypes = {}
        for column in df.columns:
            col = df[column].copy()
            col.dropna()
            if col.empty:
                continue
            sql_specification = self._determine_dtype(df, column)
            if sql_specification:
                new_dtypes[column] = sql_specification
        return new_dtypes

    def _determine_dtype(self, df, column):
        if df[column].dtype in ("object", "unicode_", "string_"):
            return self._get_varchar_spec(df, column)
        if df[column].dtype in ("float64",):
            return self._check_float_spec(df, column)
        if df[column].dtype in ("int64",):
            return self._check_integer_spec(df, column)
        logger.debug(
            f"Not intervening on dtype of column [{column}] {df[column].dtype}."
        )
        return None

    @classmethod
    def _check_float_spec(cls, df, column):
        if not df[column].apply(float.is_integer).all():
            return None
        logger.debug("Demoting column [%s] from float...", column)
        return cls._check_integer_spec(df, column)

    @classmethod
    def _check_integer_spec(cls, df, column):
        observed_range = [df[column].min(), df[column].max()]
        for sqltype in (sa.types.SMALLINT, sa.types.INT, sa.types.BIGINT):
            if cls._well_within_range(observed_range, sqltype):
                logger.debug(
                    "Column [%s] numeric type determined to be %s.", column, sqltype
                )
                return sqltype
        return None

    @classmethod
    def _well_within_range(cls, observed, sqltype):
        limit = cls.NUMERIC_RANGES[sqltype]
        # Convert to Python's int because numpy's int64 will overflow
        max_observed = int(max(abs(x) for x in observed))
        test_level = max_observed * cls.NUMERIC_PADDING_FACTOR
        valid = bool(-limit < -test_level and test_level < limit)
        return valid

    def _get_varchar_spec(self, df, column):
        try:
            stringed = df[column].str.encode(encoding="utf-8").str
        except AttributeError:
            # Not a string? Well, Pandas also keeps very long numbers as object...
            logger.debug("Very long integer in column %s?", column)
            return self.large_number_fallback
        if self.varchar_override:
            return self.varchar_override
        observed_len = stringed.len().max()
        return self._create_varchar_spec(observed_len, column, self)

    @classmethod
    def _create_varchar_spec(cls, max_length, field_name, distro):
        try:
            rounded = round_up(max_length, nearest=50)
        except ValueError:
            logger.warning("All null field %s?", field_name)
            return None
        if rounded == 0:
            logger.warning("0-length string field %s", field_name)
            return None
        if distro.varchar_max_specs > 0 and rounded > distro.varchar_max_specs:
            fallback = distro.varchar_fallback
            logger.debug("Out of range of VARCHAR length. Fallback to %s.", fallback)
            return fallback
        return sa.VARCHAR(rounded)

    @classmethod
    def get(cls, given_name):
        distro_matches = [
            subclass
            for pattern, subclass in cls._registered_distros
            if pattern.match(str(given_name))
        ]
        if len(distro_matches) != 1:
            cls._failed_to_find(given_name)
        selected_distro = distro_matches.pop()
        distro_instance = selected_distro()
        return distro_instance

    @classmethod
    def _failed_to_find(cls, given_name):
        known_distros = tuple(x.name for p, x in cls._registered_distros)
        err_msg = (
            f"Given input `{given_name}`, "
            + f"could not match distribution to known: {known_distros}"
        )
        raise SQLDistroNotFound(err_msg)

    def find(self, channel, object_pattern="%", schema_pattern="%"):

        # Lone % causes ValueError on unsupported format character 0x27
        object_pattern = object_pattern.replace(r"%", r"%%")
        schema_pattern = schema_pattern.replace(r"%", r"%%")
        object_query = self.templates["find"].format(
            schema_pattern=schema_pattern, object_pattern=object_pattern
        )
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["table_schema", "table_name"]]
        result_list = [
            Table(x.table_name, schema=x.table_schema, channel=channel)
            for x in df.itertuples(index=False)
        ]
        return result_list

    @classmethod
    def register(cls, pattern):
        def decorator(delegate):
            cls._registered_distros.append(
                (re.compile(pattern, flags=re.IGNORECASE), delegate)
            )
            return delegate

        return decorator

    def create_spec(self, *, server, database, engine_kwargs):
        raise NotImplementedError

    def create_engine(self, server, database, engine_kwargs):
        url, final_engine_kwargs = self.create_spec(
            server=server, database=database, engine_kwargs=engine_kwargs
        )
        return self._create_engine(url, **final_engine_kwargs)

    @classmethod
    def _create_engine(cls, url, **engine_kwargs):
        return sa.create_engine(url, **engine_kwargs)

    @property
    def resolver(self):
        # Must be implemented per-distro by subclass
        raise NotImplementedError

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Distro('{self.name}')"


@Distro.register(r"^(my|maria).*")
class MySQL(Distro):
    name = "mysql"
    driver = "pymysql"
    varchar_max_specs = 2 ** 16 - 101
    resolver = "{schema}.`{name}`"

    def __init__(self):
        super().__init__()
        self.varchar_fallback = self.dialect.LONGTEXT
        self.large_number_fallback = self.dialect.DOUBLE

    def create_spec(self, *, server, database, engine_kwargs):
        username = engine_kwargs.pop("username")
        password = engine_kwargs.pop("password")
        url = (
            f"{self.name}+{self.driver}:"
            + f"//{username}:{password}@"
            + f"{server}/{database}"
            + f"?charset=utf8mb4"
        )
        return (url, engine_kwargs)


@Distro.register(r"^post.*")
class PostgresQL(Distro):
    name = "postgresql"
    driver = "psycopg2"
    # resolver = '{schema}."{name}"'
    resolver = "{schema}.{name}"

    def __init__(self):
        super().__init__()
        self.large_number_fallback = self.dialect.DOUBLE_PRECISION
        self.varchar_override = self.dialect.TEXT

    def create_spec(self, *, server, database, engine_kwargs):
        username = engine_kwargs.pop("username")
        password = engine_kwargs.pop("password")
        url = f"{self.name}+{self.driver}://{username}:{password}@{server}/{database}"
        return (url, engine_kwargs)


@Distro.register(r"(^(mss|ms s|micro).*)|(.*server)")
class MSSQL(Distro):
    name = "mssql"
    driver = "pyodbc"
    minimal_keywords = ["server", "database", "schema", "name"]
    resolver = "[{database}].[{schema}].[{name}]"
    templates = Distro.templates.copy()
    __mssql_specific = {
        "find": """
            --MSSQL.find()
            select
                sch.name as [schema],
                obj.name as [name],
                type_desc,
                obj.create_date,
                obj.modify_date,
                object_id
            from {server}.{database}.sys.schemas sch
            left join {server}.{database}.sys.objects obj
            on sch.schema_id = obj.schema_id
            where sch.name like '{schema_pattern}'
            and obj.name like '{object_pattern}'
            and type_desc not like '%constraint%'
            and type_desc not in ('sql_stored_procedure');
            """
    }
    templates.update(__mssql_specific)

    def __init__(self):
        super().__init__()
        self.large_number_fallback = self.dialect.DECIMAL

    def create_spec(self, *, server, database, engine_kwargs):
        spec_dict = {
            "server": server,
            "database": database,
            "driver": "SQL Server",
            "trusted_connection": "yes",
            "autocommit": "yes",
            "executemany": "yes",
        }
        spec_string = ";".join(f"{k}={{{v}}}" for k, v in spec_dict.items())
        engine_inputs = parse.quote_plus(spec_string)

        url = f"{self.name}+{self.driver}:///?odbc_connect={engine_inputs}"

        engine_kwargs = {"encoding": "latin1"}
        engine_kwargs.update(engine_kwargs)
        return (url, engine_kwargs)

    @classmethod
    def _create_engine(cls, url, **engine_kwargs):
        engine = sa.create_engine(url, **engine_kwargs)
        cls.add_fast_executemany(engine)
        return engine

    @staticmethod
    def add_fast_executemany(engine: sa.engine.Engine):
        """ Dramatically improve pyodbc upload performance

        Theoretically, just "fast_executemany": "True" should be sufficient
        in newer versions of the driver.

        .. note ::

            Improved 1m row upload from over 7 minutes to less than 1
            under pyodbc==4.0.26, SQLAlchemy==1.3.1, pandas==0.24.2.

        """
        # pylint: disable=unused-argument, unused-variable
        @sa.event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, params, context, executemany
        ):
            if executemany:
                cursor.fast_executemany = True
                cursor.commit()

    def find(self, channel, object_pattern="%", schema_pattern="%"):

        object_query = self.templates["find"].format(
            schema_pattern=schema_pattern,
            object_pattern=object_pattern,
            server=channel.server,
            database=channel.database,
        )
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["name", "schema"]]
        result_list = [
            Table(x.name, schema=x.schema, channel=channel)
            for x in df.itertuples(index=False)
        ]
        return result_list


@Distro.register(r"^.*lite\d?")
class SQLite(Distro):
    name = "sqlite"
    driver = "sqlite3"
    resolver = "{name}"

    minimal_keywords = ["database", "name"]
    # Filenames have wholly different semantics from other SQL identifiers
    untouchable_identifiers = ["database"]

    templates = Distro.templates.copy()
    __sqlite_specific = {
        "find": """--SQLite.find()
                select name as table_name from sqlite_master
                where type = 'table' and name like '{object_pattern}';
                """
    }
    templates.update(__sqlite_specific)

    def __init__(self):
        super().__init__()
        self.varchar_override = self.dialect.TEXT

    def create_spec(self, *, server, database, engine_kwargs):
        assert True or server  # unused
        if not database or database in ("", ":memory:"):
            db_for_url = ":memory:"
        else:
            resolved = Path(database).expanduser().resolve()
            resolved.touch()
            db_for_url = str(resolved)
        url = f"{self.name}:///{db_for_url}"
        return (url, engine_kwargs)

    def find(self, channel, object_pattern="%", schema_pattern="%"):

        object_query = self.templates["find"].format(object_pattern=object_pattern)
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["table_name"]]
        result_list = [
            Table(x.table_name, channel=channel) for x in df.itertuples(index=False)
        ]
        return result_list

    def determine_dtypes(self, df):
        """SQlite does not make gradations in integers or text, so don't try."""
        return None


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

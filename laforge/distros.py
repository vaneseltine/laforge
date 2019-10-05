import logging
import math
import re
from importlib import import_module
from pathlib import Path
from urllib import parse

import sqlalchemy as sa

from .sql import Script, Table

logger = logging.getLogger(__name__)
logger.debug(logger.name)


class SQLDistroNotFound(Exception):
    pass


class Distro:
    """Base class for SQL Distros

    ..note:: http://troels.arvin.dk/db/rdbms/
    """

    driver = None
    name = "n/a"
    human_name = "n/a"

    NUMERIC_RANGES = {
        sa.types.SMALLINT: 2 ** 15 - 101,
        sa.types.INT: 2 ** 31 - 101,
        sa.types.BIGINT: 2 ** 63 - 101,
    }
    NUMERIC_PADDING_FACTOR = 10

    find_template = """--ANSI.find()
        select table_schema, table_name
        from information_schema.tables
        where table_schema like '{schema_pattern}'
            and table_name like '{object_pattern}';
        """
    untouchable_identifiers = []

    def __init__(self, _):
        try:
            import_module(self.driver)
        except ModuleNotFoundError:
            logger.warning(f"No driver ({self.driver}) to support distro {self.name}")

    def __new__(cls, name):
        retrieved_subclass = cls._get_subclass_given(name)
        return super().__new__(retrieved_subclass)

    @classmethod
    def _get_subclass_given(cls, name):
        """
        ..note :: These pop; a user-defined subclass will come up last.

        """
        distro_exact = cls._get_exact(name)
        if distro_exact:
            return distro_exact.pop()
        distro_fuzzy = cls._get_fuzzy(name)
        if len(distro_fuzzy) != 1:
            cls._fail_to_find_requested_distro(name)
        return distro_fuzzy.pop()

    @classmethod
    def _get_exact(cls, s):
        return [x for x in cls.__subclasses__() if x.name.lower() == str(s).lower()]

    @classmethod
    def _get_fuzzy(cls, s):
        return [
            x
            for x in cls.__subclasses__()
            if re.match(x.regex, str(s), flags=re.IGNORECASE)
        ]

    @classmethod
    def _fail_to_find_requested_distro(cls, given_name):
        err_msg = (
            f"Given input `{given_name}`, "
            + f"could not match distribution to known: {cls.known()}"
        )
        raise SQLDistroNotFound(err_msg)

    @classmethod
    def known(cls):
        return {x.name: x.human_name for x in cls.__subclasses__()}

    def determine_dtypes(self, df):
        new_dtypes = {}
        for column in df.columns:
            col = df[column].copy()
            col.dropna()
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

    @classmethod
    def _get_varchar_spec(cls, df, column):
        try:
            stringed = df[column].str.encode(encoding="utf-8").str
        except AttributeError:
            return None
        observed_len = stringed.len().max()
        return cls._create_varchar_spec(observed_len)

    @staticmethod
    def _create_varchar_spec(max_length):
        try:
            rounded = round_up(max_length, nearest=50)
        except ValueError:
            return None
        return sa.VARCHAR(rounded)

    def find(self, channel, object_pattern="%", schema_pattern="%"):

        # Lone % causes ValueError on unsupported format character 0x27
        object_pattern = object_pattern.replace(r"%", r"%%")
        schema_pattern = schema_pattern.replace(r"%", r"%%")
        object_query = self.find_template.format(
            schema_pattern=schema_pattern, object_pattern=object_pattern
        )
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["table_schema", "table_name"]]
        result_list = [
            Table(x.table_name, schema=x.table_schema, channel=channel)
            for x in df.itertuples(index=False)
        ]
        return result_list

    def create_spec(self, *, server, database, engine_kwargs):
        raise NotImplementedError

    def create_engine(self, *, server, database, engine_kwargs):
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


class MySQL(Distro):
    name = "mysql"
    human_name = "MySQL/MariaDB"
    regex = "^(my|maria).*"
    driver = "pymysql"
    resolver = "{schema}.`{name}`"

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


class PostgresQL(Distro):
    name = "postgresql"
    human_name = "PostgreSQL"
    regex = r"^post.*"
    driver = "psycopg2"
    resolver = "{schema}.{name}"

    def create_spec(self, *, server, database, engine_kwargs):
        username = engine_kwargs.pop("username")
        password = engine_kwargs.pop("password")
        url = f"{self.name}+{self.driver}://{username}:{password}@{server}/{database}"
        return (url, engine_kwargs)


class MSSQL(Distro):
    name = "mssql"
    human_name = "Microsoft SQL Server"
    regex = r"(^(mss|ms s|micro).*)|(.*server)"
    driver = "pyodbc"
    resolver = "[{database}].[{schema}].[{name}]"
    find_template = """--MSSQL.find()
        select
            sch.name as [schema],
            obj.name as [name],
            type_desc,
            obj.create_date,
            obj.modify_date,
            object_id
        from {database}.sys.schemas sch
        left join {database}.sys.objects obj
        on sch.schema_id = obj.schema_id
        where sch.name like '{schema_pattern}'
        and obj.name like '{object_pattern}'
        and type_desc not like '%constraint%'
        and type_desc not in ('sql_stored_procedure');
        """

    def create_spec(self, *, server, database, engine_kwargs):
        # https://docs.sqlalchemy.org/en/13/dialects/mssql.html
        spec_dict = {
            "server": server,
            "database": database,
            "driver": "SQL Server",
            "fast_executemany": "yes",
            "autocommit": "yes",
        }
        if "driver" in engine_kwargs:
            spec_dict["driver"] = engine_kwargs.pop("driver")
        if "username" in engine_kwargs and "password" in engine_kwargs:
            spec_dict["UID"] = engine_kwargs.pop("username")
            spec_dict["PWD"] = engine_kwargs.pop("password")
        else:
            spec_dict["trusted_connection"] = "yes"

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

        object_query = self.find_template.format(
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


class SQLite(Distro):
    name = "sqlite"
    human_name = "SQLite"
    regex = r"^.*lite\d?"
    driver = "sqlite3"
    resolver = "{name}"

    # Filenames have wholly different semantics from other SQL identifiers
    untouchable_identifiers = ["database"]

    find_template = """--SQLite.find()
        select name as table_name from sqlite_master
        where type = 'table' and name like '{object_pattern}';
        """

    def create_spec(self, *, server, database, engine_kwargs):
        # pylint: disable=unused-argument # server unneeded
        if not database or re.match("[^a-z]*memory[^a-z]*", str(database).lower()):
            final_database = ":memory:"
        else:
            resolved = Path(database).expanduser().resolve()
            resolved.touch()
            final_database = str(resolved)
        url = f"{self.name}:///{final_database}"
        return (url, engine_kwargs)

    def find(self, channel, object_pattern="%", schema_pattern="%"):
        object_query = self.find_template.format(object_pattern=object_pattern)
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["table_name"]]
        result_list = [
            Table(x.table_name, channel=channel) for x in df.itertuples(index=False)
        ]
        return result_list

    def determine_dtypes(self, df):
        """SQlite does not make gradations in integers or text, so don't try."""
        return None


def round_up(n, nearest=1):
    """Round up ``n`` to the nearest ``nearest``.

    :param n:
    :param nearest:  (Default value = 1)

    """
    return nearest * math.ceil(n / nearest)

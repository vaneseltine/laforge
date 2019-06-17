import logging
import re

from importlib import import_module
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    # Generic,
    List,
    Mapping,
    NoReturn,
    Optional,
    Pattern,
    Sequence,
    Tuple,
    Type,
    # TypeVar,
    Union,
)
from urllib import parse

import pandas as pd
import sqlalchemy as sa

from .sql import Channel, Script, Table
from .toolbox import round_up

logger = logging.getLogger(__name__)
logger.debug(__name__)


class SQLDistroNotFoundError(Exception):
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
    minimal_keywords: List[str] = ["server", "schema", "name"]
    untouchable_identifiers: List[str] = []
    varchar_fallback = None
    varchar_max_specs: int = -1
    varchar_override = None

    templates = {
        "find": """--Distro.find()
            select table_schema, table_name
            from information_schema.tables
            where table_schema like '{schema_pattern}'
                and table_name like '{object_pattern}';
            """
    }

    _registered_distros: List[Tuple[Pattern, Any]] = []  # type: ignore

    def __init__(self) -> None:
        import_module(self.driver)
        self.dialect = import_module(f"sqlalchemy.dialects.{self.name}")

    def determine_dtypes(self, df: pd.DataFrame) -> Optional[Dict[Any, Any]]:
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

    def _determine_dtype(
        self, df: pd.DataFrame, column: str
    ) -> Optional[sa.sql.type_api.TypeEngine]:
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
    def _check_float_spec(
        cls, df: pd.DataFrame, column: str
    ) -> Union[None, sa.types.Integer, sa.types.BigInteger]:
        if not df[column].apply(float.is_integer).all():
            return None
        logger.debug("Demoting column [%s] from float...", column)
        return cls._check_integer_spec(df, column)

    @classmethod
    def _check_integer_spec(
        cls, df: pd.DataFrame, column: str
    ) -> Union[None, sa.types.Integer, sa.types.BigInteger]:
        observed_range = [df[column].min(), df[column].max()]
        for sqltype in (sa.types.SMALLINT, sa.types.INT, sa.types.BIGINT):
            if cls._well_within_range(observed_range, sqltype):
                logger.debug(
                    "Column [%s] numeric type determined to be %s.", column, sqltype
                )
                return sqltype
        return None

    @classmethod
    def _well_within_range(
        cls, observed: Sequence[int], sqltype: sa.sql.type_api.TypeEngine
    ) -> bool:
        limit = cls.NUMERIC_RANGES[sqltype]
        # Convert to Python's int because numpy's int64 will overflow
        max_observed = int(max(abs(x) for x in observed))
        test_level = max_observed * cls.NUMERIC_PADDING_FACTOR
        valid = bool(-limit < -test_level and test_level < limit)
        return valid

    def _get_varchar_spec(
        self, df: pd.DataFrame, column: str
    ) -> Optional[sa.sql.type_api.TypeEngine]:
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
    def _create_varchar_spec(
        cls, max_length: int, field_name: str, distro: Any
    ) -> Optional[sa.sql.type_api.TypeEngine]:
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
    def get(cls, given_name: Any) -> Any:
        distro_matches: List[Type[Any]] = [
            subclass
            for pattern, subclass in cls._registered_distros
            if pattern.match(str(given_name))
        ]
        if len(distro_matches) != 1:
            cls._failed_to_find(given_name)
        selected_distro: Type[Any] = distro_matches.pop()
        distro_instance: Any = selected_distro()
        return distro_instance

    @classmethod
    def _failed_to_find(cls, given_name: str) -> NoReturn:
        known_distros = tuple(x.name for p, x in cls._registered_distros)
        err_msg = (
            f"Given input `{given_name}`, "
            + f"could not match distribution to known: {known_distros}"
        )
        raise SQLDistroNotFoundError(err_msg)

    def find(
        self, channel: Channel, object_pattern: str = "%", schema_pattern: str = "%"
    ) -> List[Table]:

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
    def register(cls, pattern: str) -> Callable[..., Type[Any]]:
        def decorator(delegate: Type[Any]) -> Type[Any]:
            cls._registered_distros.append(
                (re.compile(pattern, flags=re.IGNORECASE), delegate)
            )
            return delegate

        return decorator

    def create_spec(
        self,
        *,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> Tuple[str, Mapping[str, str]]:
        raise NotImplementedError

    def create_engine(
        self,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> sa.engine.Engine:
        url, final_engine_kwargs = self.create_spec(
            server=server, database=database, engine_kwargs=engine_kwargs
        )
        return self._create_engine(url, **final_engine_kwargs)

    @classmethod
    def _create_engine(
        cls, url: str, **engine_kwargs: Mapping[str, Any]
    ) -> sa.engine.Engine:
        return sa.create_engine(url, **engine_kwargs)

    @property
    def resolver(self) -> str:
        # Must be implemented per-distro by subclass
        raise NotImplementedError

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Distro('{self.name}')"


@Distro.register(r"^(my|maria).*")
class MySQL(Distro):
    name = "mysql"
    driver = "pymysql"
    varchar_max_specs = 2 ** 16 - 101
    resolver = "{schema}.`{name}`"

    def __init__(self) -> None:
        super().__init__()
        self.varchar_fallback = self.dialect.LONGTEXT  # type: ignore
        self.large_number_fallback = self.dialect.DOUBLE  # type: ignore

    def create_spec(
        self,
        *,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> Tuple[str, Mapping[str, str]]:
        username = engine_kwargs.pop("username")
        password = engine_kwargs.pop("password")
        url = f"{self.name}+{self.driver}://{username}:{password}@{server}/{database}?charset=utf8mb4"
        return (url, engine_kwargs)


@Distro.register(r"^post.*")
class PostgresQL(Distro):
    name = "postgresql"
    driver = "psycopg2"
    # resolver = '{schema}."{name}"'
    resolver = "{schema}.{name}"

    def __init__(self) -> None:
        super().__init__()
        self.large_number_fallback = self.dialect.DOUBLE_PRECISION  # type: ignore
        self.varchar_override = self.dialect.TEXT  # type: ignore

    def create_spec(
        self,
        *,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> Tuple[str, Mapping[str, str]]:
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

    def __init__(self) -> None:
        super().__init__()
        self.large_number_fallback = self.dialect.DECIMAL  # type: ignore

    def create_spec(
        self,
        *,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> Tuple[str, Mapping[str, str]]:
        spec_dict: Dict[str, Union[str, None]] = {
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
    def _create_engine(
        cls, url: str, **engine_kwargs: Mapping[str, Any]
    ) -> sa.engine.Engine:
        engine = sa.create_engine(url, **engine_kwargs)
        cls.add_fast_executemany(engine)
        return engine

    @staticmethod
    def add_fast_executemany(engine: sa.engine.Engine) -> None:
        """ Dramatically improve pyodbc upload performance

        Theoretically, just "fast_executemany": "True" should be sufficient
        in newer versions of the driver.

        .. note ::

            Improved 1m row upload from over 7 minutes to less than 1
            under pyodbc==4.0.26, SQLAlchemy==1.3.1, pandas==0.24.2.

        """
        # pylint: disable=unused-argument, unused-variable
        @sa.event.listens_for(engine, "before_cursor_execute")  # type: ignore
        def receive_before_cursor_execute(  # type: ignore
            conn, cursor, statement, params, context, executemany
        ) -> None:
            if executemany:
                cursor.fast_executemany = True
                cursor.commit()

    def find(
        self, channel: Channel, object_pattern: str = "%", schema_pattern: str = "%"
    ) -> List[Table]:

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

    minimal_keywords: List[str] = ["database", "name"]
    # Filenames have wholly different semantics from other SQL identifiers
    untouchable_identifiers: List[str] = ["database"]

    templates = Distro.templates.copy()
    __sqlite_specific = {
        "find": """--SQLite.find()
                select name as table_name from sqlite_master
                where type = 'table' and name like '{object_pattern}';
                """
    }
    templates.update(__sqlite_specific)

    def __init__(self) -> None:
        super().__init__()
        self.varchar_override = self.dialect.TEXT  # type: ignore

    def create_spec(
        self,
        *,
        server: Optional[str],
        database: Optional[str],
        engine_kwargs: Dict[str, Any],
    ) -> Tuple[str, Mapping[str, str]]:
        assert True or server  # unused
        if not database or database in ("", ":memory:"):
            db_for_url = ":memory:"
        else:
            resolved = Path(database).expanduser().resolve()
            resolved.touch()
            db_for_url = str(resolved)
        url = f"{self.name}:///{db_for_url}"
        return (url, engine_kwargs)

    def find(
        self, channel: Channel, object_pattern: str = "%", schema_pattern: str = "%"
    ) -> List[Table]:

        object_query = self.templates["find"].format(object_pattern=object_pattern)
        object_script = Script(object_query, channel=channel)
        df = object_script.to_table()[["table_name"]]
        result_list = [
            Table(x.table_name, channel=channel) for x in df.itertuples(index=False)
        ]
        return result_list

    def determine_dtypes(self, df: pd.DataFrame) -> None:
        """SQlite does not make gradations in integers or text, so don't try."""
        return None

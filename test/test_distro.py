import pandas as pd
import pytest
import sqlalchemy as sa

from laforge.distros import Distro, SQLDistroNotFound


class TestDistroGet:
    def t_get_exactly_one_distro_canonically(self, test_distro):
        try:
            result = Distro.get(test_distro)
            assert test_distro.lower() == result.name.lower()
        except ModuleNotFoundError:
            pytest.skip(f"Missing {test_distro} module.")

    @pytest.mark.parametrize(
        "canonical, incoming",
        [
            ("mssql", "mssql"),
            ("mssql", "microsoft sql server"),
            ("mssql", "microsoft sql"),
            ("mssql", "ms sql"),
            ("mssql", "sql server"),
            ("mssql", "sql server 14.0"),
            ("mssql", "microsoft sql server 15.0"),
            ("mysql", "mysql"),
            ("mysql", "my sql"),
            ("mysql", "maria"),
            ("mysql", "mariadb"),
            ("mysql", "maria db"),
            ("postgresql", "postgresql"),
            ("postgresql", "post gre"),
            ("postgresql", "postgre"),
            ("sqlite", "sqlite3"),
            ("sqlite", "sqlite"),
        ],
    )
    def t_get_exactly_one_distro_variants(self, canonical, incoming, test_distro):
        if canonical != test_distro:
            pytest.skip("")
        assert Distro.get(incoming).name == canonical
        assert Distro.get(incoming.upper()).name == canonical

    @pytest.mark.parametrize("badname", ["", 293, "asdf"])
    def t_fail_bad_distros(self, badname):
        with pytest.raises(SQLDistroNotFound):
            Distro.get(badname)

    @pytest.mark.parametrize(
        "vaguename", ["sql", "m sql", "MSQL", "MYSQL SERVER", "SQLITE SERVER"]
    )
    def t_fail_vague_distros(self, vaguename):
        with pytest.raises(SQLDistroNotFound):
            Distro.get(vaguename)


class KeyReturner:
    @staticmethod
    def pop(key):
        return str(key)


class TestDistroCreation:
    @pytest.mark.parametrize("db", ["", ":memory:", "sqlite.db"])
    def t_sqlite_prepare_engine(self, db, tmp_path):
        result = Distro.get("sqlite")
        if db == "sqlite.db":
            db = tmp_path / "sqlite.db"
        url, _ = result.create_spec(server="srvr", database=db, engine_kwargs={})
        assert str(db or ":memory:") in url

    def t_prepare_for_other_engines(self, test_distro):
        if test_distro == "sqlite":
            pytest.skip("sqlite handled elsewhere")
        try:
            result = Distro.get(test_distro)
        except ModuleNotFoundError:
            pytest.skip(f"Missing {test_distro} module.")
        url, _ = result.create_spec(
            server="srvr", database="db", engine_kwargs=KeyReturner
        )
        assert test_distro in url


class TestDistroFunctionality:
    @pytest.mark.parametrize("dtype", [int, pd.np.int64, pd.np.float64])
    @pytest.mark.parametrize("factor", [1, 10, 100])
    @pytest.mark.parametrize("i", [2 ** 31 - 1, 2 ** 31, 2 ** 63 - 1, 2 ** 63, 2 ** 64])
    def t_no_integer_overflow_from_numpy(self, dtype, factor, i):
        """
        numpy int64 can't handle overflow (but does issue warning)
        """
        with pytest.warns(None) as record:
            Distro.NUMERIC_PADDING_FACTOR = factor
            try:
                sequence = [dtype(i)] * 2
            except OverflowError:
                return None
            Distro._well_within_range(sequence, sa.types.INT)
        assert len(record) == 0
